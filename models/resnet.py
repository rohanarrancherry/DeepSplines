#!/usr/bin/env python3

'''ResNet in PyTorch.

Reference:
[1] Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
    Deep Residual Learning for Image Recognition. arXiv:1512.03385

Based on:
- Pytorch implementation
- https://github.com/akamaster/pytorch_resnet_cifar10
'''

import torch
import torch.nn as nn
import torch.nn.functional as F
import sys

from models.basemodel import BaseModel


__all__ = ['ResNet20', 'ResNet32', 'ResNet44']


def conv3x3(in_planes, out_planes, stride=1, groups=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                    padding=1, groups=groups, bias=False)


def conv1x1(in_planes, out_planes, stride=1):
    """1x1 convolution"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)



class BasicBlock(BaseModel):
    expansion = 1

    def __init__(self, in_planes, planes, stride=1, downsample=None, **params):
        """
        Args:
            in_planes : number of input in_channels
            planes : number of output channels after first convolution
            downsample : None or downsample/channel_augmentation strategy
        """
        super().__init__(**params)

        self.dropout_rate = 0 # change if needed
        activation_specs = [] # stores layer type ('conv'/'linear') and number of channels for each activation layer

        # Both self.conv1 and self.downsample layers downsample the input when stride != 1
        self.conv1 = conv3x3(in_planes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        activation_specs.append(('conv', planes))

        self.dropout = nn.Dropout(p=self.dropout_rate)

        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        activation_specs.append(('conv', planes))

        self.downsample = downsample
        self.stride = stride
        self.activations = self.init_activation_list(activation_specs, bias=False)


    def forward(self, x):
        """ """
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.activations[0](out)

        out = self.dropout(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.activations[1](out)

        return out



class Bottleneck(BaseModel):
    expansion = 4

    def __init__(self, in_planes, planes, stride=1, downsample=None, **params):
        """
        Args:
            in_planes : number of input in_channels
            planes : number of output channels after first convolution
            downsample : None or downsample/channel_augmentation strategy
        """
        super().__init__(**params)

        # stores layer type ('conv'/'linear') and number of channels/neurons for each layer
        activation_specs = []

        self.conv1 = conv1x1(in_planes, planes)
        self.bn1 = nn.BatchNorm2d(planes)
        activation_specs.append(('conv', planes))

        # Both self.conv2 and self.downsample layers downsample the input when stride != 1
        self.conv2 = conv3x3(planes, planes, stride)
        self.bn2 = nn.BatchNorm2d(planes)
        activation_specs.append(('conv', planes))

        self.conv3 = conv1x1(planes, self.expansion * planes)
        self.bn3 = nn.BatchNorm2d(self.expansion * planes)
        activation_specs.append(('conv', self.expansion * planes))

        self.downsample = downsample
        self.stride = stride
        self.activations = self.init_activation_list(activation_specs, bias=False)


    def forward(self, x):
        """ """
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.activations[0](out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.activations[1](out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.activations[2](out)

        return out



class ResNet(BaseModel):
    def __init__(self, block, num_blocks, in_planes=64, **params):
        """ """
        super().__init__(**params)

        self.in_planes = in_planes
        self.layer0 = self._make_layer0(in_planes)
        self.layer1 = self._make_layer(block, in_planes,  num_blocks[0])

        planes = in_planes * 2
        self.layer2 = self._make_layer(block, planes, num_blocks[1], stride=2)

        planes *= 2
        self.layer3 = self._make_layer(block, planes, num_blocks[2], stride=2)

        self.layer4 = None
        if len(num_blocks) > 3:
            planes *= 2
            self.layer4 = self._make_layer(block, planes, num_blocks[3], stride=2)

        self.avgpool2d = nn.AdaptiveAvgPool2d((1, 1))
        self.linear = nn.Linear(planes * block.expansion, self.num_classes)

        self.initialization(init_type='He') # Kaiming He initialization
        self.num_params = self.get_num_params()


    def _make_layer0(self, in_planes):
        """ """
        if self.dataset_name.startswith('cifar'):
            layer0 = nn.Sequential(
                nn.Conv2d(3, in_planes, kernel_size=3, stride=1, padding=1, bias=False),
                nn.BatchNorm2d(in_planes),
                self.init_activation(('conv', in_planes), bias=False)
            )
        else:
            layer0 = nn.Sequential(
                 nn.Conv2d(3, in_planes, kernel_size=7, stride=2, padding=3, bias=False),
                 nn.BatchNorm2d(in_planes),
                 self.init_activation(('conv', in_planes), bias=False),
                 nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
            )

        return layer0


    def _make_layer(self, block, planes, num_blocks, stride=1):
        """ """
        downsample = None
        if stride != 1 or self.in_planes != planes * block.expansion:
            downsample = nn.Sequential(
                conv1x1(self.in_planes, block.expansion * planes, stride),
                nn.BatchNorm2d(planes * block.expansion)
            )

        layers = []
        # First layer block, before adding to output in the skip-connection:
        # layers 2,3,4 - need to increase number of filters of identity + downsample.
        layers.append(block(self.in_planes, planes, stride, downsample, **self.params))
        self.in_planes = planes * block.expansion

        for _ in range(1, num_blocks):
            # no downsampling, stride=1
            layers.append(block(self.in_planes, planes, **self.params))

        return nn.Sequential(*layers)


    def forward(self, x):
        """ """
        # cifar size: 32x32
        out = self.layer0(x)
        # cifar size: 32x32
        out = self.layer1(out)
        # cifar size: 32x32
        out = self.layer2(out)
        # cifar size: 16x16
        out = self.layer3(out)
        # cifar size: 8x8
        if self.layer4 is not None:
            out = self.layer4(out)
            # cifar size: 4x4

        out = self.avgpool2d(out) # global avg pool of kernel_size HxW
        out = self.linear(out.view(out.size(0), -1))

        return out


################################################################################

def ResNet20(**params):
    return ResNet(BasicBlock, [3, 3, 3], in_planes=16, **params)

def ResNet32(**params):
    return ResNet(BasicBlock, [5, 5, 5], in_planes=16, **params)

def ResNet44(**params):
    return ResNet(BasicBlock, [7, 7, 7], in_planes=16, **params)