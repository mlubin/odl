# Copyright 2014, 2015 The ODL development group
#
# This file is part of ODL.
#
# ODL is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ODL is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ODL.  If not, see <http://www.gnu.org/licenses/>.

"""Spaces of functions with common domain and range.

TODO: document properly
"""

# Imports for common Python 2/3 codebase
from __future__ import print_function, division, absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import super

# External imports
import numpy as np

# ODL imports
from odl.operator.operator import Operator
from odl.set.domain import IntervalProd
from odl.set.sets import RealNumbers, ComplexNumbers, Set
from odl.set.space import LinearSpace


__all__ = ('FunctionSet', 'FunctionSpace')


def _apply_not_impl(*_):
    """Dummy function to be used when apply function is not given."""
    raise NotImplementedError('no `_apply` method defined.')


class FunctionSet(Set):

    """A general set of functions with common domain and range."""

    def __init__(self, domain, range):
        """Initialize a new instance.

        Parameters
        ----------
        domain : `Set`
            The domain of the functions.
        range : `Set`
            The range of the functions.
        """
        if not isinstance(domain, Set):
            raise TypeError('domain {!r} not a `Set` instance.'.format(domain))

        if not isinstance(range, Set):
            raise TypeError('range {!r} not a `Set` instance.'.format(range))

        self._domain = domain
        self._range = range

    @property
    def domain(self):
        """Common domain of all functions in this set."""
        return self._domain

    @property
    def range(self):
        """Common range of all functions in this set."""
        return self._range

    def element(self, fcall, fapply=None, vectorization='none'):
        """Create a `FunctionSet` element.

        Parameters
        ----------
        fcall : callable
            The actual instruction for out-of-place evaluation. If
            `fcall` is a `FunctionSet.Vector`, its `_call`, `_apply`
            and `vectorization` are used for initialization unless
            explicitly given
        fapply : callable, optional
            The actual instruction for in-place evaluation
        vectorization : {'none', 'array', 'meshgrid'}
            Vectorization type of this function.

            'none' : no vectorized evaluation

            'array' : vectorized evaluation on an array of
            domain elements. Requires domain to be an
            `IntervalProd` instance.

            'meshgrid' : vectorized evaluation on a meshgrid
            tuple of arrays. Requires domain to be an
            `IntervalProd` instance.

        *At least one of the arguments `fcall` and `fapply` must
        be provided.*

        Returns
        -------
        element : `FunctionSet.Vector`
            The new element created from `fcall` and `fapply`

        See also
        --------
        discr.grid.TensorGrid.meshgrid : efficient grids for function
        evaluation
        """
        if isinstance(fcall, self.Vector):  # no double wrapping
            if fapply is None:
                if vectorization == fcall.vectorization:
                    return fcall
                else:
                    vectorization = fcall.vectorization
                    fapply = fcall._apply
                    fcall = fcall._call
                    return self.Vector(self, fcall, fapply,
                                       vectorization=vectorization)
        else:
            return self.Vector(self, fcall, fapply,
                               vectorization=vectorization)

    def __eq__(self, other):
        """`s.__eq__(other) <==> s == other`.

        Returns
        -------
        equals : `bool`
            `True` if `other` is a `FunctionSet` with same `domain`
            and `range`, `False` otherwise.
        """
        if other is self:
            return True

        return (isinstance(other, FunctionSet) and
                self.domain == other.domain and
                self.range == other.range)

    def __contains__(self, other):
        """`s.__contains__(other) <==> other in s`.

        Returns
        -------
        equals : `bool`
            `True` if `other` is a `FunctionSet.Vector` whose `space`
            attribute equals this space, `False` otherwise.
        """
        return (isinstance(other, FunctionSet.Vector) and
                self == other.space)

    def __repr__(self):
        """`s.__repr__() <==> repr(s)`."""
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.domain, self.range)

    def __str__(self):
        """`s.__str__() <==> str(s)`."""
        return '{}({}, {})'.format(self.__class__.__name__,
                                   self.domain, self.range)

    class Vector(Operator):

        """Representation of a `FunctionSet` element."""

        def __init__(self, fset, fcall, fapply=None, vectorization='none'):
            """Initialize a new instance.

            Parameters
            ----------
            fset : `FunctionSet`
                The set of functions this element lives in
            fcall : callable
                The actual instruction for out-of-place evaluation. If
                `fcall` is a `FunctionSet.Vector`, its `_call`, `_apply`
                and `vectorization` are used for initialization unless
                explicitly given as arguments
            fapply : callable, optional
                The actual instruction for in-place evaluation. This is
                possible only for vectorized functions.
            vectorization : {'none', 'array', 'meshgrid'}
                Vectorization type of this function.

                'none' : no vectorized evaluation

                'array' : vectorized evaluation on an array of
                domain elements. Requires domain to be an
                `IntervalProd` instance.

                'meshgrid' : vectorized evaluation on a meshgrid
                tuple of arrays. Requires domain to be an
                `IntervalProd` instance.

            See also
            --------
            discr.grid.TensorGrid.meshgrid : efficient grids for
            function evaluation
            """
            if not isinstance(fset, FunctionSet):
                raise TypeError('function set {!r} is not a `FunctionSet` '
                                'instance.'.format(fset))
            if not callable(fcall):
                raise TypeError('call function {} is not callable.'
                                ''.format(fcall))
            if fapply is not None and not callable(fapply):
                raise TypeError('apply function {} is not callable.'
                                ''.format(fapply))
            self._vectorization = str(vectorization).lower()
            if self._vectorization not in ('none', 'array', 'meshgrid'):
                raise ValueError('vectorization type {!r} not understood.'
                                 ''.format(vectorization))
            if self._vectorization == 'none' and fapply is not None:
                raise ValueError('in-place function evaluation only possible '
                                 'for vectorized functions.')
            if (self._vectorization != 'none' and
                    not isinstance(fset.domain, IntervalProd)):
                raise TypeError('vectorization requires the function set '
                                'domain to be an `IntervalProd` instance, '
                                'got {!r}.'.format(fset.domain))

            super().__init__(fset.domain, fset.range, linear=False)
            self._space = fset
            self._call = fcall
            self._apply = fapply if fapply is not None else _apply_not_impl

        @property
        def space(self):
            """Return `space` attribute."""
            return self._space

        @property
        def domain(self):
            """The function domain (abstract in `Operator`)."""
            return self.space.domain

        @property
        def range(self):
            """The function range (abstract in `Operator`)."""
            return self.space.range

        @property
        def vectorization(self):
            """Vectorization type of this function."""
            return self._vectorization

        def _vectorized_input_check(self, x, vec_bounds_check):
            """Check if vectorized `x` lies in `domain`."""
            if self.vectorization == 'array':
                # Expected: (N, d) array of points, where d = dimension
                if not isinstance(x, np.ndarray):
                    raise TypeError('input {!r} not a `numpy.ndarray` '
                                    'instance'.format(x))
                if not (x.ndim == 2 and x.shape[1] == self.domain.ndim):
                    raise ValueError('expected input shape (n, {}) for '
                                     'some n, got {}.'
                                     ''.format(self.domain.ndim, x.shape))
                if vec_bounds_check:
                    # Can be expensive for large arrays
                    min_coords = np.min(x, axis=0)
                    max_coords = np.max(x, axis=0)

            elif self.vectorization == 'meshgrid':
                # Expected: d meshgrid type arrays
                if not all(isinstance(xi, np.ndarray) for xi in x):
                    raise TypeError('input {!r} not a `numpy.ndarray` '
                                    'sequence.')
                if len(x) != self.domain.ndim:
                    raise ValueError('expected {} meshgrid arrays, got {}.'
                                     ''.format(self.domain.ndim, len(x)))
                if vec_bounds_check:
                    # This is comparably cheap
                    min_coords = [np.min(vec) for vec in x]
                    max_coords = [np.max(vec) for vec in x]
            else:
                raise TypeError('invalid vectorized input {}.'.format(x))

            if vec_bounds_check:
                if (min_coords not in self.domain or
                        max_coords not in self.domain):
                    raise ValueError('input contains points outside the '
                                     'valid domain {}.'.format(self.domain))

        def __call__(self, x, **kwargs):
            """Out-of-place evaluation.

            Parameters
            ----------
            x : object
                Input argument for the function evaluation. Conditions
                on `x` depend on the type of vectorization:

                'none' : `x` must be a domain element

                'array' : `x` must be a `numpy.ndarray` with `x[i]`
                being a domain element for each `i`

                'meshgrid' : `x` must be a sequence of `numpy.ndarray`
                with length `space.ndim`, and each array must lie within
                the boundaries of the interval for the corresponding
                axis in `space.domain`.

            kwargs : {'vec_bounds_check'}
                'vec_bounds_check' : bool
                    Whether or not to check if all input points lie in
                    the function domain in the case of vectorized
                    evaluation.
                    Default: `True`

            Returns
            -------
            out : range element or array of elements
                Result of the function evaluation

            Raises
            ------
            TypeError
                If `x` is not a valid vectorized evaluation argument

                If `out` is not a range element or a `numpy.ndarray`
                of range elements

            ValueError
                If evaluation points fall outside the valid domain
            """
            vec_bounds_check = kwargs.pop('vec_bounds_check', True)

            if self.vectorization == 'none':
                if x not in self.domain:
                    raise TypeError('input {!r} not in domain '
                                    '{}.'.format(x, self.domain))
            else:
                self._vectorized_input_check(x, vec_bounds_check)

            out = self._call(x)

            if self.vectorization == 'none':
                if out not in self.range:
                    raise TypeError('output {!r} not in range {}.'
                                    ''.format(out, self.range))
            else:
                if not (isinstance(out, np.ndarray) and
                        out.flat[0] in self.range):
                    raise TypeError('output {!r} not an array of elements '
                                    'of the function range {}.'
                                    ''.format(out, self.range))
            return out

        def apply(self, x, out, **kwargs):
            """Vectorized and multi-argument in-place evaluation.

            Parameters
            ----------
            x : object
                Input argument for the function evaluation. Conditions
                on `x` depend on the type of vectorization:

                'none' : `x` must be a domain element

                'array' : `x` must be a `numpy.ndarray` with `x[i]`
                being a domain element for each `i`

                'meshgrid' : `x` must be a sequence of `numpy.ndarray`
                with length `space.ndim`, and each array must lie within
                the boundaries of the interval for the corresponding
                axis in `space.domain`.

            out : object
                Outuput argument holding the result of the function
                evaluation. Conditions on `out` depend on whether this
                function allows vectorization:

                'none' : `out` must be a range element

                'array' or 'meshgrid' : `out` is a `numpy.ndarray`
                with size `n`, where `n` is the total number of
                evaluation points represented by `x`.


            kwargs : {'vec_bounds_check'}
                'vec_bounds_check' : bool
                    Whether or not to check if all input points lie in
                    the function domain in the case of vectorized
                    evaluation.
                    Default: `True`

            Returns
            -------
            None

            Raises
            ------
            TypeError
                If `x` is not a valid vectorized evaluation argument

                If `out` is not a range element or a `numpy.ndarray`
                of range elements

            ValueError
                If evaluation points fall outside the valid domain
            """
            vec_bounds_check = kwargs.pop('vec_bounds_check', True)

            if self.vectorization == 'none':
                if x not in self.domain:
                    raise TypeError('input {!r} not in domain '
                                    '{}.'.format(x, self.domain))
                if out not in self.range:
                    raise TypeError('output {!r} not in range {}.'
                                    ''.format(out, self.range))
            else:
                self._vectorized_input_check(x, vec_bounds_check)
                if not (isinstance(out, np.ndarray) and
                        out.flat[0] in self.range):
                    raise TypeError('output {!r} not an array of elements '
                                    'of the function range {}.'
                                    ''.format(out, self.range))
            self._apply(x, out)

        def assign(self, other):
            """Assign `other` to this vector.

            This is implemented without `lincomb` to ensure that
            `vec == other` evaluates to `True` after
            `vec.assign(other)`.
            """
            if other not in self.space:
                raise TypeError('vector {!r} is not an element of the space '
                                '{} of this vector.'
                                ''.format(other, self.space))
            self._call = other._call
            self._apply = other._apply
            self._vectorization = other._vectorization

        def __eq__(self, other):
            """`vec.__eq__(other) <==> vec == other`.

            Returns
            -------
            equals : `bool`
                `True` if `other` is a `FunctionSet.Vector` with
                `other.space` equal to this vector's space and
                the call and apply implementations of `other` and
                this vector are equal. `False` otherwise.
            """
            if other is self:
                return True

            return (isinstance(other, FunctionSet.Vector) and
                    self.space == other.space and
                    self._call == other._call and
                    self._apply == other._apply and
                    self.vectorization == other.vectorization)

        def __ne__(self, other):
            """`vec.__ne__(other) <==> vec != other`"""
            return not self.__eq__(other)

        def __str__(self):
            if self._call is not None:
                return str(self._call)
            else:
                return str(self._apply_impl)

        def __repr__(self):
            inner_fstr = '{!r}'
            if self._apply is not None:
                inner_fstr += ', fapply={fapply!r}'
            if self.vectorization != 'none':
                inner_fstr += ', vectorization={vect!r}'

            inner_str = inner_fstr.format(self._call, fapply=self._apply,
                                          vect=self.vectorization)

            return '{!r}.element({})'.format(self.space, inner_str)


class FunctionSpace(FunctionSet, LinearSpace):

    """A vector space of functions."""

    def __init__(self, domain, field):
        """Initialize a new instance.

        Parameters
        ----------
        domain : `Set`
            The domain of the functions.
        field : `RealNumbers` or `ComplexNumbers`
            The range of the functions.
        """
        if not isinstance(domain, Set):
            raise TypeError('domain {!r} not a `Set` instance.'.format(domain))
        if not isinstance(field, (RealNumbers, ComplexNumbers)):
            raise TypeError('field {!r} not a `RealNumbers` or '
                            '`ComplexNumbers` instance.'.format(field))

        super().__init__(domain, field)
        self._field = field

    @property
    def field(self):
        """Return `field` attribute."""
        return self._field

    def element(self, fcall=None, fapply=None, vectorization='none'):
        """Create a `FunctionSet` element.

        Parameters
        ----------
        fcall : callable, optional
            The actual instruction for out-of-place evaluation. If
            `fcall` is a `FunctionSet.Vector`, its `_call`, `_apply`
            and `vectorization` are used for initialization unless
            explicitly given.
            If `fcall` is `None`, the zero function is created.
        fapply : callable, optional
            The actual instruction for in-place evaluation
        vectorization : {'none', 'array', 'meshgrid'}
            Vectorization type of this function.

            'none' : no vectorized evaluation

            'array' : vectorized evaluation on an array of
            domain elements. Requires domain to be an
            `IntervalProd` instance.

            'meshgrid' : vectorized evaluation on a meshgrid
            tuple of arrays. Requires domain to be an
            `IntervalProd` instance.

        Returns
        -------
        `element` : `FunctionSpace.Vector`
            The new element.
        """
        if fcall is None:
            return self.zero(vectorization=vectorization)
        else:
            return super().element(fcall, fapply, vectorization=vectorization)

    def zero(self, vectorization='none'):
        """The function mapping everything to zero.

        Since `lincomb` is slow, we implement this function directly.
        This function is the additive unit in the function space.

        Parameters
        ----------
        vectorization : {'none', 'array', 'meshgrid'}
            Vectorization type of this function.

            'none' : no vectorized evaluation

            'array' : vectorized evaluation on an array of
            domain elements. Requires domain to be an
            `IntervalProd` instance.

            'meshgrid' : vectorized evaluation on a meshgrid
            tuple of arrays. Requires domain to be an
            `IntervalProd` instance.
        """
        dtype = float if self.field == RealNumbers() else complex
        vectorization = str(vectorization).lower()
        if vectorization not in ('none', 'array', 'meshgrid'):
            raise ValueError('vectorization type {!r} not understood.'
                             ''.format(vectorization))

        def zero_novec(_):
            """The zero function, non-vectorized."""
            return dtype(0.0)

        def zero_arr(x):
            """The zero function, vectorized for arrays."""
            return np.zeros(x.shape[0], dtype=dtype)

        def zero_mg(x):
            """The zero function, vectorized for meshgrids."""
            bc = np.broadcast(*x)
            if all(xi.flags.c_contiguous for xi in x):
                order = 'C'
            elif all(xi.flags.f_contiguous for xi in x):
                order = 'F'
            else:
                raise ValueError('inconsistent ordering of meshgrid '
                                 'arrays.')
            return np.zeros(bc.shape, dtype=dtype, order=order)

        if vectorization == 'none':
            zero_func = zero_novec
        elif vectorization == 'array':
            zero_func = zero_arr
        else:
            zero_func = zero_mg
        return self.element(zero_func, vectorization=vectorization)

    def one(self, vectorization='none'):
        """The function mapping everything to one.

        This function is the multiplicative unit in the function space.

        Parameters
        ----------
        vectorization : {'none', 'array', 'meshgrid'}
            Vectorization type of this function.

            'none' : no vectorized evaluation

            'array' : vectorized evaluation on an array of
            domain elements. Requires domain to be an
            `IntervalProd` instance.

            'meshgrid' : vectorized evaluation on a meshgrid
            tuple of arrays. Requires domain to be an
            `IntervalProd` instance.
        """
        dtype = float if self.field == RealNumbers() else complex
        vectorization = str(vectorization).lower()
        if vectorization not in ('none', 'array', 'meshgrid'):
            raise ValueError('vectorization type {!r} not understood.'
                             ''.format(vectorization))

        def one_novec(_):
            """The one function, non-vectorized."""
            return dtype(1.0)

        def one_arr(x):
            """The one function, vectorized for arrays."""
            return np.ones(x.shape[0], dtype=dtype)

        def one_mg(x):
            """The one function, vectorized for meshgrids."""
            bc = np.broadcast(*x)
            if all(xi.flags.c_contiguous for xi in x):
                order = 'C'
            elif all(xi.flags.f_contiguous for xi in x):
                order = 'F'
            else:
                raise ValueError('inconsistent ordering of meshgrid '
                                 'arrays.')
            return np.ones(bc.shape, dtype=dtype, order=order)

        if vectorization == 'none':
            one_func = one_novec
        elif vectorization == 'array':
            one_func = one_arr
        else:
            one_func = one_mg
        return self.element(one_func, vectorization=vectorization)

    def __eq__(self, other):
        """`s.__eq__(other) <==> s == other`.

        Returns
        -------
        equals : `bool`
            `True` if `other` is a `FunctionSpace` with same `domain`
            and `range`, `False` otherwise.
        """
        if other is self:
            return True

        return (isinstance(other, FunctionSpace) and
                self.domain == other.domain and
                self.range == other.range)

    def _lincomb(self, a, x1, b, x2, out):
        """Raw linear combination of `x1` and `x2`.

        Note
        ----
        The additions and multiplications are implemented via a simple
        Python function, so the resulting function is probably slow.

        Different vectorization types are not allowed.
        """
        # Store to allow aliasing
        x1_old_call = x1._call
        x1_old_apply = x1._apply
        x2_old_call = x2._call
        x2_old_apply = x2._apply

        def lincomb_call(x):
            """Linear combination, call version."""
            # Due to vectorization, at least one call must be made to
            # ensure the correct final shape. The rest is optimized as
            # far as possible.
            if a == 0 and b != 0:
                out = x2_old_call(x)
                if b != 1:
                    out *= b
            elif b == 0:  # Contains the case a == 0
                out = x1_old_call(x)
                if a != 1:
                    out *= a
            else:
                out = x1_old_call(x)
                if a != 1:
                    out *= a
                tmp = x2_old_call(x)
                if b != 1:
                    tmp *= b
                out += tmp

            return out

        def lincomb_apply(x, out):
            """Linear combination, apply version."""
            if not isinstance(out, np.ndarray):
                raise TypeError('in-place evaluation only possible if output '
                                'is of type `numpy.ndarray`.')
            if a == 0 and b == 0:
                out *= 0
            elif a == 0 and b != 0:
                x2_old_apply(x, out)
                if b != 1:
                    out *= b
            elif b == 0 and a != 0:
                x1_old_apply(x, out)
                if a != 1:
                    out *= a
            else:
                tmp = np.empty_like(out)
                x1_old_apply(x, out)
                x2_old_apply(x, tmp)
                if a != 1:
                    out *= a
                if b != 1:
                    tmp *= b

                out += tmp

        out._call = lincomb_call
        # If one of the summands' apply method is undefined, it will not be
        # defined in the result either
        if _apply_not_impl in (x1._apply, x2._apply):
            out._apply = _apply_not_impl
        else:
            out._apply = lincomb_apply

    def lincomb(self, a, x1, b=None, x2=None, out=None):
        """Same as in LinearSpace.Vector, but with vectorization."""
        if a not in self.field:
            raise TypeError('first scalar {!r} not in the field {!r} of the '
                            'space {!r}.'.format(a, self.field, self))
        if x1 not in self:
            raise TypeError('first input vector {!r} not in space {!r}.'
                            ''.format(x1, self))
        if out is None:
            out = self.element(vectorization=x1.vectorization)
        else:
            if out not in self:
                raise TypeError('output vector {!r} not in space {!r}.'
                                ''.format(out, self))
            if out.vectorization != x1.vectorization:
                raise ValueError('incompatible vectorization types in first '
                                 'input vector {!r} and output vector {!r} '
                                 '({!r} != {!r}).'
                                 ''.format(x1, out, x1.vectorization,
                                           out.vectorization))
        if b is None:  # Single argument
            if x2 is not None:
                raise ValueError('second input vector provided but no '
                                 'second scalar.')
            # Call method
            return self._lincomb(a, x1, 0, x1, out)
        else:  # Two arguments
            if b not in self.field:
                raise TypeError('second scalar {!r} not in the field {!r} of '
                                'the space {!r}.'.format(b, self.field, self))
            if x2 not in self:
                raise TypeError('second input vector {!r} not in space {!r}.'
                                ''.format(x2, self))
            if x2.vectorization != x1.vectorization:
                raise ValueError('incompatible vectorization types in first '
                                 'input vector {!r} and second input vector '
                                 '{!r} ({!r} != {!r}).'
                                 ''.format(x1, x2, x1.vectorization,
                                           x2.vectorization))
            # Call method
            return self._lincomb(a, x1, b, x2, out)

    def _multiply(self, x1, x2, out):
        """Raw pointwise multiplication of two functions.

        Note
        ----
        The multiplication is implemented with a simple Python
        function, so the resulting function object is probably slow.
        """
        x1_old_call = x1._call
        x1_old_apply = x1._apply
        x2_old_call = x2._call
        x2_old_apply = x2._apply

        def product_call(x):
            """The product call function."""
            return x1_old_call(x) * x2_old_call(x)

        def product_apply(x, out):
            """The product apply function."""
            tmp = np.empty_like(out)
            x1_old_apply(x, out)
            x2_old_apply(x, tmp)
            out *= tmp

        out._call = product_call
        # If one of the factors' apply method is undefined, it will not be
        # defined in the result either
        if _apply_not_impl in (x1._apply, x2._apply):
            out._apply = _apply_not_impl
        else:
            out._apply = product_apply

    def multiply(self, x1, x2, out=None):
        """Same as in LinearSpace.Vector, but with vectorization."""
        if x1 not in self:
            raise TypeError('first vector {!r} not in space {!r}'
                            ''.format(x1, self))
        if x2 not in self:
            raise TypeError('second vector {!r} not in space {!r}'
                            ''.format(x2, self))
        if x2.vectorization != x1.vectorization:
            raise ValueError('incompatible vectorization types in first '
                             'input vector {!r} and second input vector '
                             '{!r} ({!r} != {!r}).'
                             ''.format(x1, x2, x1.vectorization,
                                       x2.vectorization))
        if out is None:
            out = self.element(vectorization=x1.vectorization)
        else:
            if out not in self:
                raise TypeError('ouput vector {!r} not in space {!r}'
                                ''.format(out, self))
            if out.vectorization != x1.vectorization:
                raise ValueError('incompatible vectorization types in first '
                                 'input vector {!r} and output vector {!r} '
                                 '({!r} != {!r}).'
                                 ''.format(x1, out, x1.vectorization,
                                           out.vectorization))
        self._multiply(x1, x2, out)

    def _divide(self, x1, x2, out):
        """Raw pointwise division of two functions."""
        x1_old_call = x1._call
        x1_old_apply = x1._apply
        x2_old_call = x2._call
        x2_old_apply = x2._apply

        def quotient_call(x):
            """The quotient call function."""
            return x1_old_call(x) / x2_old_call(x)

        def quotient_apply(x, out):
            """The quotient apply function."""
            tmp = np.empty_like(out)
            x1_old_apply(x, out)
            x2_old_apply(x, tmp)
            out /= tmp

        out._call = quotient_call
        # If one of the factors' apply method is undefined, it will not be
        # defined in the result either
        if _apply_not_impl in (x1._apply, x2._apply):
            out._apply = _apply_not_impl
        else:
            out._apply = quotient_apply

    def divide(self, x1, x2, out=None):
        """Same as in LinearSpace.Vector, but with vectorization."""
        if x1 not in self:
            raise TypeError('first vector {!r} not in space {!r}'
                            ''.format(x1, self))
        if x2 not in self:
            raise TypeError('second vector {!r} not in space {!r}'
                            ''.format(x2, self))
        if x2.vectorization != x1.vectorization:
            raise ValueError('incompatible vectorization types in first '
                             'input vector {!r} and second input vector '
                             '{!r} ({!r} != {!r}).'
                             ''.format(x1, x2, x1.vectorization,
                                       x2.vectorization))
        if out is None:
            out = self.element(vectorization=x1.vectorization)
        else:
            if out not in self:
                raise TypeError('ouput vector {!r} not in space {!r}'
                                ''.format(out, self))
            if out.vectorization != x1.vectorization:
                raise ValueError('incompatible vectorization types in first '
                                 'input vector {!r} and output vector {!r} '
                                 '({!r} != {!r}).'
                                 ''.format(x1, out, x1.vectorization,
                                           out.vectorization))
        self._divide(x1, x2, out)

    class Vector(FunctionSet.Vector, LinearSpace.Vector):

        """Representation of a `FunctionSpace` element."""

        def __init__(self, fspace, fcall=None, fapply=None,
                     vectorization='none'):
            """Initialize a new instance.

            Parameters
            ----------
            fspace : `FunctionSpace`
                The set of functions this element lives in
            fcall : callable
                The actual instruction for out-of-place evaluation. If
                `fcall` is a `FunctionSet.Vector`, its `_call`, `_apply`
                and `vectorization` are used for initialization unless
                explicitly given
            fapply : callable, optional
                The actual instruction for in-place evaluation
            vectorization : {'none', 'array', 'meshgrid'}
                Vectorization type of this function.

                'none' : no vectorized evaluation

                'array' : vectorized evaluation on an array of
                domain elements. Requires domain to be an
                `IntervalProd` instance.

                'meshgrid' : vectorized evaluation on a meshgrid
                tuple of arrays. Requires domain to be an
                `IntervalProd` instance.

            *At least one of the arguments `fcall` and `fapply` must
            be provided.*
            """
            if not isinstance(fspace, FunctionSpace):
                raise TypeError('function space {} not a `FunctionSpace` '
                                'instance.'.format(fspace))

            super().__init__(fspace, fcall, fapply,
                             vectorization=vectorization)

        # Convenience functions using element() need to be adapted
        def copy(self):
            """Create an identical (deep) copy of this vector."""
            result = self.space.element(vectorization=self.vectorization)
            result.assign(self)
            return result

        def __add__(self, other):
            """`f.__add__(other) <==> f + other`."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.lincomb(1, self, 1, other, out=out)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.lincomb(1, self, 1, other * one, out=out)
            return out

        def __radd__(self, other):
            """`f.__radd__(other) <==> other + f`."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.lincomb(1, other, 1, self, out=out)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.lincomb(1, other * one, 1, self, out=out)
            return out

        def __iadd__(self, other):
            """`f.__iadd__(other) <==> f += other`."""
            if other in self.space:
                self.space.lincomb(1, self, 1, other, out=self)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.lincomb(1, self, 1, other * one, out=self)
            return self

        def __sub__(self, other):
            """Implementation of 'self - other'."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.lincomb(1, self, -1, other, out=out)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.lincomb(1, self, 1, -other * one, out=out)
            return out

        def __rsub__(self, other):
            """`f.__rsub__(other) <==> other - f`."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.lincomb(1, other, -1, self, out=out)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.lincomb(1, other * one, -1, self, out=out)
            return out

        def __isub__(self, other):
            """`f.__isub__(other) <==> f -= other`."""
            if other in self.space:
                self.space.lincomb(1, self, -1, other, out=self)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.lincomb(1, self, 1, -other * one, out=self)
            return self

        def __mul__(self, other):
            """`f.__mul__(other) <==> f * other`."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.multiply(self, other, out=out)
            else:
                self.space.lincomb(other, self, out=out)
            return out

        def __rmul__(self, other):
            """`f.__rmul__(other) <==> other * f`."""
            return self.__mul__(other)
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.multiply(other, self, out=out)
            else:
                self.space.lincomb(other, self, out=out)
            return out

        def __imul__(self, other):
            """`f.__imul__(other) <==> f *= other`."""
            if other in self.space:
                self.space.multiply(self, other, out=self)
            else:
                self.space.lincomb(other, self, out=self)
            return self

        def __truediv__(self, other):
            """`f.__truediv__(other) <==> f / other` (true division)."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.divide(self, other, out=out)
            else:
                self.space.lincomb(1./other, self, out=out)
            return out

        def __div__(self, other):
            """`f.__div__(other) <==> f / other`."""
            return self.__truediv__(other)

        def __rtruediv__(self, other):
            """`f.__rtruediv__(other) <==> other / f` (true division)."""
            out = self.space.element(vectorization=self.vectorization)
            if other in self.space:
                self.space.divide(other, self, out=out)
            else:
                one = self.space.one(vectorization=self.vectorization)
                self.space.divide(other * one, self, out=out)
            return out

        def __rdiv__(self, other):
            """`f.__rdiv__(other) <==> other / f`."""
            return self.__rtruediv__(other)

        def __itruediv__(self, other):
            """`f.__itruediv__(other) <==> f /= other` (true division)."""
            if other in self.space:
                self.space.divide(self, other, out=self)
            else:
                self.space.lincomb(1./other, self, out=self)
            return self

        def __idiv__(self, other):
            """`f.__idiv__(other) <==> f /= other`."""
            return self.__itruediv__(other)

        def __pow__(self, n):
            """`f.__pow__(n) <==> f ** n`."""
            n = int(n)
            tmp = self.copy()
            for i in range(n):
                self.space.multiply(tmp, self, out=tmp)
            return tmp

        def __ipow__(self, n):
            """`f.__ipow__(n) <==> f **= n`."""
            n = int(n)
            if n == 1:
                return self
            elif n % 2 == 0:
                self.space.multiply(self, self, out=self)
                return self.__ipow__(n//2)
            else:
                tmp = self.copy()
                for i in range(n):
                    self.space.multiply(tmp, self, out=tmp)
                return tmp

        def __neg__(self):
            """`f.__neg__() <==> -f`."""
            out = self.space.element(vectorization=self.vectorization)
            self.space.lincomb(-1.0, self, out=out)
            return out

        def __pos__(self):
            """`f.__pos__() <==> +f`."""
            return self.copy()


if __name__ == '__main__':
    from doctest import testmod, NORMALIZE_WHITESPACE
    testmod(optionflags=NORMALIZE_WHITESPACE)
