"""
This module implements deepBsplines with an added explicit linear term,
giving more flexibility to the activations (might produce better results)
in some contexts.

(For more details, see deepBspline_base.py.)
"""

import torch
from torch import nn
from torch.nn import functional as F
from models.deepBspline_base import DeepBSplineBase



class DeepBSplineExplicitLinear(DeepBSplineBase):
    """
    nn.Module for DeepBspline activation functions with an added
    linear term.
    """

    def __init__(self, bias=True, **kwargs):
        """
        Args:
            bias : (flag) learn bias (default: True)
        """
        super().__init__(**kwargs)
        self.learn_bias = bias # flag

        # tensor with locations of spline coefficients
        grid_tensor = self.grid_tensor # size: (num_activations, size)
        coefficients = torch.zeros_like(grid_tensor) # spline coefficients
        # linear coefficients
        spline_bias = torch.zeros(self.num_activations).to(**self.device_type) # b0
        spline_weight = torch.zeros_like(spline_bias) # b1

        if self.init == 'leaky_relu':
            spline_weight.fill_(0.01) # b1 = 0.01
            coefficients = F.leaky_relu(grid_tensor, negative_slope=0.01) \
                            - (0.01 * grid_tensor)

        elif self.init == 'relu':
            coefficients = F.relu(grid_tensor)

        elif self.init == 'even_odd':
            # initalize half of the activations with an even function (abs) and
            # and the other half with an odd function (soft threshold).
            half = self.num_activations // 2
            # absolute value
            spline_weight[0:half].fill_(-1.)
            coefficients[0:half, :] = (grid_tensor[0:half, :]).abs() \
                                        - (-1. * grid_tensor[0:half, :])
            # soft threshold
            spline_weight[half::].fill_(1.) # for soft threshold
            spline_bias[half::].fill_(0.5)
            coefficients[half::, :] = F.softshrink(grid_tensor[half::, :], lambd=0.5) \
                                        - (1. * grid_tensor[half::, :] + 0.5)
        else:
            raise ValueError('init should be in [leaky_relu, relu, even_odd].')

        # Need to vectorize coefficients to perform specific operations
        self._coefficients_vect = nn.Parameter(coefficients.contiguous().view(-1)) # size: (num_activations*size)
        self.spline_weight = nn.Parameter(spline_weight) # size: (num_activations,)

        if self.learn_bias is True:
            self.spline_bias = nn.Parameter(spline_bias) # size: (num_activations,)
        else:
            self.spline_bias = spline_bias



    @property
    def coefficients_vect(self):
        """ B-spline vectorized coefficients. """
        return self._coefficients_vect


    @staticmethod
    def parameter_names(**kwargs):
        """ Yield names of the module parameters """
        for name in ['coefficients_vect', 'spline_weight', 'spline_bias']:
            yield name


    @property
    def weight(self):
        return self.spline_weight


    @property
    def bias(self):
        return self.spline_bias



    def forward(self, input):
        """
        Args:
            input (torch.Tensor):
                2D or 4D, depending on weather the layer is
                convolutional ('conv') or fully-connected ('fc')

        Returns:
            output (torch.Tensor)
        """
        input_size = input.size()
        output = super().forward(input)

        x = self.reshape_forward(input)
        b0 = self.spline_bias.view((1, -1, 1, 1))
        b1 = self.spline_weight.view((1, -1, 1, 1))

        out_linear = b0 + b1 * x
        output = output + self.reshape_back(out_linear, input_size)

        return output



    def extra_repr(self):
        """ repr for print(model) """

        s = ('mode={mode}, num_activations={num_activations}, init={init}, '
            'size={size}, grid={grid[0]}, bias={learn_bias}.')

        return s.format(**self.__dict__)
