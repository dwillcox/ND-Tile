"""
The Plane_nd class defines functions for 
fitting an n-dimensional plane to data values 
in an n-dimensional independent variable parameter space.


```
# Example
xvec = np.linspace(0, 10)
yvec = np.linspace(0, 10)
zvec = np.linspace(0, 10)
xx, yy, zz = np.meshgrid(xvec, yvec, zvec)
dvars = 5 + 2*xx + 3*yy + 4*zz
xflat = xx.flatten()
yflat = yy.flatten()
zflat = zz.flatten()
ivflat = np.transpose(np.array([xflat, yflat, zflat]))
dvflat = dvars.flatten()

fitter = Plane_nd(ivflat, dvflat, 3)

fitter.dolsq()
```

Copyright (c) 2016, Donald E. Willcox
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""    

import numpy as np
from scipy.optimize import leastsq

class Plane_nd(object):
    def __init__(self, ivals, dvals, dm):
        self.ivals = ivals
        self.dvals = dvals
        self.dm = dm
        self.npars = self.dm+1
        self.npts = len(self.dvals)
        self.ndf = self.npts - self.npars

    def zcoord(self, x):
        # Return padded coordinate vector for multiplying
        # by the plane coefficients by prepending 1
        # to the coordinate vector to multiply against
        # the constant plane coefficient.
        z = np.empty(self.npars)
        z[1:self.npars] = x[0:self.dm]
        z[0] = 1.0
        return z
    
    def fplane(self, x, *cpars):
        cpars = np.array(cpars)
        z = self.zcoord(x)
        return np.sum(z * cpars)

    def objfun(self, pars):
        # Objective function for the least squares fit.
        # Returns a vector of the fit errors given parameters.
        fvals = np.array([dv - self.fplane(iv,pars) for dv, iv in zip(self.dvals, self.ivals)])
        return fvals

    def objjac(self, pars):
        # Jacobian of the objective function wrt parameters
        # Returns a matrix with derivatives across rows
        # and independent variable points along columns.
        jac = np.array([-self.zcoord(iv) for iv in self.ivals])
        return jac

    def dolsq(self, guess=[], do_print=False):
        if list(guess):
            # If guess is provided, it should provide a vector for the initial values xini
            xini = np.copy(guess)
        else:
            xini = np.zeros(self.npars)
            xini[0] = np.average(self.dvals)
            # Find independent values at average of dependent var
            iave = np.abs(self.dvals-xini[0]).argmin()
            ivt = np.transpose(self.ivals)
            for i in np.arange(1, self.npars):
                ivti = ivt[i-1]
                # Find maximum value along independent axis
                iv_max_i = ivti.argmax()
                iv_max = ivti[iv_max_i]
                # Find corresponding dependent variable value
                dv_max = self.dvals[iv_max_i]
                # Find minimum value along independent axis
                iv_min_i = ivti.argmin()
                iv_min = ivti[iv_min_i]
                # Find corresponding dependent variable value
                dv_min = self.dvals[iv_min_i]
                # Estimate slope
                xini[i] = (dv_max - dv_min)/(iv_max - iv_min)/self.dm
        popt, pcov, idict, mesg, ierr = leastsq(self.objfun, xini, Dfun=self.objjac,
                                                    full_output=True, xtol=1.e-20, ftol=1.e-16)
        # pcov is derived from the jacobian around the solution. It will be None if it's a singular matrix.
        # A singular matrix, or pcov = None, indicates flat curvature in some direction.
        # Multiply by residual variance to obtain parameter covariance.
        resd = self.objfun(popt)
        if self.ndf > 0 and pcov is not None:
            # Residual variance calculation. NDF = # POINTS - # FIT PARS. resd_var
            resd_var = np.sum(resd**2)/self.ndf
            pcovariance = pcov * resd_var
            perr = np.sqrt(np.diag(pcovariance))
        else:
            perr = [None for di in range(self.npars)]
        if do_print:
            print(popt)
            print(perr)
            for k in idict.keys():
                print('{}: {}'.format(k, idict[k]))
            print(mesg)
            print(ierr)
        return popt, perr



