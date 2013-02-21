import sys 
import site 
import os.path
	
your_env_package_dir = '/home/kjetil/pyenvs/greetr/lib/python2.7/site-packages'

# Add site-packages directory
site.addsitedir(your_env_package_dir)

# Boot application
app_path = os.path.dirname(__file__)
sys.path.insert(0, app_path)
from greetr import app as application
