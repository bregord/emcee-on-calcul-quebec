# In[1]:

import numpy as np
#import matplotlib.pyplot as plt
#import matplotlib.cm as cm
import time
import emcee
from emcee.utils import MPIPool
import sys

pi = np.pi


# In[2]:

N = 3601  # DON'T ADJUST, Number of data points
l_t,h_t = 0.0,6.0  # DON'T ADJUST, Low and high time values
polyO_in = 7  # DON'T ADJUST, Generative polynomial order

##### Loading with columns: time,x0_noisy,y0_noisy,data_noisy [and x0,y0,A(t),D(x0,y0),data]
data_Ary = np.load('data/A_dataset.npy')  ### LOAD DATA ARRAY HERE ###

T = data_Ary[:,0]
xNt_vals = data_Ary[:,1]
yNt_vals = data_Ary[:,2]
Y_d = data_Ary[:,3]

params_true = np.load('data/A_params.npy')  ### LOAD TRUE PARAMETERS HERE ###
Ast_true,Ecl_true,DCs_true,SigF_true = params_true[0:3],params_true[3:6],params_true[6:-1],np.array([params_true[-1]])
# True Detector Coefficients order: [y^n*x^0, y^n-1*x^0, ..., y^n-1*x^1, y^n-2*x^1, ..., x^n] (NO y^0*x^0 TERM)


# In[3]:

def perf_astro_model(t_low,t_high,t_sing,astro,ecl):
    # astro[]: 0 amplitude, 1 frequency, 2 phase shift
    a_mdl = (astro[0]*(-np.cos(t_sing*2.0*pi*astro[1]/(t_high - t_low) +
                               astro[2])) + 1.0)
    # ecl[]: 0 center, 1 half-width, 2 depth
    occult = np.logical_and((ecl[0] - ecl[1])<=t_sing,t_sing<=(ecl[0] + ecl[1]))
    a_mdl[occult] -= ecl[2]
    a_mdl[occult] = np.mean(a_mdl[occult])
    return a_mdl


# In[4]:

def perf_detect_model(x_o,y_o,dC_A,n_data):  # dC_A = detector Coefficient Array
    d_mdl = np.polynomial.polynomial.polyval2d(x_o-15.0,y_o-15.0,dC_A)
    return d_mdl


# In[5]:

# Output (i.e. fit) detector poly
polyO_out = 2  # Adjust to whatever order polynomial you'd like
temp_UTout_i = np.triu_indices(polyO_out+1)  # Including constant
UTout_i = (temp_UTout_i[0],polyO_out - temp_UTout_i[1])  # Reflecting to upper-left triangular
C_UTout = np.zeros((polyO_out+1,polyO_out+1))  # Blank coefficient array


# In[ ]:

# Setting up some output polynomial things
Cn_out = int((polyO_out+2)*(polyO_out+1)/2) - 1  # Fit C's needed; minus 1 because offset is now fixed

cn_out_Vector = np.zeros(Cn_out+1)  # Output poly Cn holder
cn_out_Vector[polyO_out] = 1.0  # Fix the offset term to 1.0


# In[6]:

# Coefficient prior
pri_DCoeff = np.array([[0.1],[-0.1]])*np.ones(Cn_out)

# Astro, Eclipse, and SigF priors
pri_AstEcl = np.array([[10.0*Ast_true[0],1.0,2.0*pi,h_t,(h_t - l_t),100.0*Ecl_true[2]],
                       [0.1*Ast_true[0],0.001,0,l_t,0.0,0.0]])
pri_SigF = np.array([[100.0*SigF_true[0]],[0.0]])


# In[8]:

P_rP = np.concatenate((pri_AstEcl,pri_DCoeff,pri_SigF),axis=1)  # Full Prior, for emcee


# In[9]:

def data_like(theta,t_sing,y_d,n_data): # theta has: 3A, 3E, #C, 1SF
    astro = theta[:3]
    ecl = theta[3:6]
    y_ast = perf_astro_model(l_t,h_t,t_sing,astro,ecl)

    cn_out_Vector[:polyO_out] = theta[6:6+polyO_out]
    cn_out_Vector[polyO_out+1:] = theta[6+polyO_out:6+Cn_out]

    C_UTout[UTout_i] = cn_out_Vector
    d_model = perf_detect_model(xNt_vals,yNt_vals,C_UTout,n_data)

    numer = y_d - (y_ast*d_model)
    sF = theta[-1:]
    lglike = -n_data*np.log(sF) - 0.5*np.sum((numer/sF)**2.0)
    return lglike


# In[10]:

def data_prior(theta,pri_span):
    if np.all(theta < pri_span[0]) and np.all(theta > pri_span[1]):
        return 0.0
    return -np.inf

def sig_below_Zero(theta):
    if theta[-1] <= 0:
        return True
    return False

def data_post(theta,t_sing,y_d,n_data,pri_span):
    if sig_below_Zero(theta) == True:
        return -np.inf
    lgpri = data_prior(theta,pri_span)
    if not np.isfinite(lgpri):
        return -np.inf
    return lgpri + data_like(theta,t_sing,y_d,n_data)


# In[11]:

# Because fit poly can have different dimension than real poly
DCs_fit_true = np.zeros(Cn_out)
pcl_i = 0  # DON'T ADJUST
pcl_bump = 0  # DON'T ADJUST, To increase lookup index after c_00 term
inout_diff = polyO_in - polyO_out
for x in np.linspace(polyO_out,0,polyO_out+1):  # In or out poly can be larger since indexes work either way!
    for y in np.linspace(x,0,x+1):
        if (y == 0) and (polyO_out-x == 0):  # Avoid c_00 term
            pcl_bump = 1
        else:
            if ((y + (polyO_out - x)) > polyO_in):
                DCs_fit_true[pcl_i] = 1e-4  # Not 0.0 to avoid stacking walkers on top of each other
            else:
                DCs_fit_true[pcl_i] = DCs_true[pcl_i + pcl_bump + inout_diff*(polyO_out + 1 - x)]
            pcl_i += 1
pcl_i,pcl_bump = 0,0  # 'Refreshing'


pool = MPIPool()

if not pool.is_master():
    # Wait for instructions from the master process.
    pool.wait()
    sys.exit(0)


# In[12]:

### Dimensions, walkers, and pre-setting direction of walker deviations
ndimP,nwalkersP = 6+Cn_out+1,4*(6+Cn_out+1)  # 6AstEcl + #Cn + 1SigF

ndimP = ndimP*2
nwalkersP = ndimP*4

r_AstEcl,r_DCoeff,r_SigF = np.random.randn(6),np.random.randn(Cn_out),np.random.randn(1)
rdev_P = np.concatenate((r_AstEcl,r_DCoeff,r_SigF))

o_AstEcl = np.random.randn(nwalkersP*6).reshape(nwalkersP,6)
o_DCoeff = np.random.randn(nwalkersP*Cn_out).reshape(nwalkersP,Cn_out)
o_SigF = np.random.randn(nwalkersP).reshape(nwalkersP,1)

off_P = np.concatenate((o_AstEcl,o_DCoeff,o_SigF),axis=1)
real_P = np.concatenate((Ast_true,Ecl_true,DCs_fit_true,SigF_true))


# In[13]:

### Apply the above!
r_scaling = 1e-3  # Percentage away from real parameters (i.e. center of walkers' ball); set as desired
o_scaling = 1e-4  # Percentage away from offset parameters (i.e. size of walkers' ball); set as desired

p0P = real_P*(1.0 + r_scaling*rdev_P)
pZP = p0P*(1.0 + o_scaling*off_P)


# In[14]:
### Run emcee
search_S = 2e6 # Number of MCMC steps to run
samplerP = emcee.EnsembleSampler(nwalkersP,ndimP,data_post,args=[T,Y_d,N,P_rP], pool=pool)
posP,probP,stateP = samplerP.run_mcmc(pZP,int(search_S));

pool.close()


print(u"Mean acceptance fraction: ", np.mean(samplerP.acceptance_fraction))

