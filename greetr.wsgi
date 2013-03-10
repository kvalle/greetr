import sys
import site
import os.path

# Add custom site-packages directory
your_env_package_dir = '/home/your-user/.virtualenvs/greetr/lib/python2.7/site-packages'
site.addsitedir(your_env_package_dir)

# Add greetr to system path
app_path = os.path.dirname(__file__)
sys.path.insert(0, app_path)

# Import greetr
from greetr import app as application
