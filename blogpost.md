Serving Python Webapps With Apache
===

Python is a great language that is useful for many things. Especially for writing web applications.
There is a [plethora of great web frameworks](http://wiki.python.org/moin/WebFrameworks) out there, and Python makes it nice and easy to do such things as [parsing json](http://docs.python.org/2/library/json.html) or [talking over HTTP](http://docs.python.org/2/library/httplib.html#module-httplib) out of the box.

If you don't need anyting fancy, Python even makes starting a simple HTTP server a one-liner from the command line:

```bash
$ python -m SimpleHTTPServer
Serving HTTP on 0.0.0.0 port 8000 ...
```

Once you need to set up a production environment, however, you will generally require something more robust to serve your application than this, or any of the development servers included with your favorite web framework.
In this blogpost I'll explain how to set up an [Apache HTTP Server](http://httpd.apache.org/) to serve Python web applications.

### Some Preliminary Setup

The steps of this tutorial will be based on an Ubuntu 12.10 setup with Python 2.7, and we'll be installing the Ubuntu flavour of Apache 2.2.
If you use a different configuration, then some details might differ, but the steps should still generally be the same.

The first thing we will need to install are couple of handy tools for working with Python development: [pip](http://www.pip-installer.org/en/latest/) and [virtualenv](http://www.virtualenv.org/en/latest/).
If you are already familiar with these, and know how to use them, skip ahead to the next section.

```bash
$ sudo apt-get install python-virtualenv
$ sudo apt-get install python-pip
$ sudo apt-get install virtualenvwrapper
```

In addition we'll also want to add the following lines to our `~/.bashrc` file, to help [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) work it's magic:

```bash
export WORKON_HOME=/opt/python-environments
source /usr/local/bin/virtualenvwrapper.sh
```

With these tools installed, we create a directory in which we will place our Python environment.
This should be the same directory we just specified in the `.bashrc` file.

```bash
$ mkdir -p /opt/python-environments
```

Next we simply tell `virtualenv` to create a new environment for us.

```bash
$ mkvirtualenv greetr
```

Now we have a fresh virtual Python environment named `greetr`, which will hold the example application we'll be installing.
Lets have a look at that next.

### The Example

For purposes of this tutorial, I have created a simple example application.
It is called Greetr, and is little more than a glorified "Hello World".
It is, however, a working Python web app, written within the [Flask framework](http://flask.pocoo.org/).

If your preferred Python web framework is something other than Flask, such as [Pyramid](http://www.pylonsproject.org/), [web2py](http://www.web2py.com/), [Django](https://www.djangoproject.com/), or any other, don't worry.
Chances are it supports the common standard for interfacing web servers and Python apps known as [WSGI](http://wsgi.readthedocs.org/en/latest/), the *Web Server Gateway Interface*, and the configuration should be similar to what we'll do here.

Now, if you like, check out [the greetr applicaton](https://github.com/kvalle/greetr).
It is a small application, simply showing a picture of a smiling robot along with a random greeting.
The main point is to serve as a basis for the examples in this tutorial, and to give you a fully functional web application to verify the setup after completing the tutorial.

Let's start by cloning the sample application down from GitHub:

```bash
$ git clone git://github.com/kvalle/greetr.git
$ cd greetr
```

Next we'll need to install the dependencies.
First make sure you have the correct environment activated:

```bash
$ workon greetr
```

Then use pip to install everything specified in [requirements.txt](https://github.com/kvalle/greetr/blob/master/requirements.txt).

```bash
$ pip install -r requirements.txt
```

Before we move on to installing and configuring Apache, lets check that everything is working.
Start Flask's embedded webserver using the provided script:

```bash
$ ./runserver.py
```

Then visit Greetr at [http://127.0.0.1:5000/](http://127.0.0.1:5000/). The app should be working, so lets move on to se how we can serve it using Apache.

### Install Apache

First, if you haven't already, install Apache along with the `mod_wsgi` module.

```bash
$ sudo apt-get install apache2 libapache2-mod-wsgi
```

Once installed, also make sure the module is activated, and that Apache is running.

```bash
$ sudo a2enmod wsgi
$ sudo service apache2 start
```

### The WSGI-file

The first thing we need to do, is to make Apache understand how to serve our application by defining the file called `greetr.wsgi`.
The `.wsgi` file contains everything necessary for Apaches `mod_wsgi` to instantiate and serve the application.

This is what [greetr.wsgi](https://github.com/kvalle/greetr/blob/master/greetr.wsgi) looks like:

```python
import sys
import site
import os.path

# Add custom site-packages directory
your_env_package_dir = '/opt/python-environments/greetr/lib/python2.7/site-packages'
site.addsitedir(your_env_package_dir)

# Add greetr to system path
app_path = os.path.dirname(__file__)
sys.path.insert(0, app_path)

# Import greetr
from greetr import app as application
```

So, what happens here?

First, since Apache won't be able to autodetect the wsgi-file within our custom python environment, we need to manually make the installed module available.
We do this by specifying the path to our python environment folder, and calling `site.addsitedir`.

Secondly, we add the location of `greetr` to Pythons system path.

Finally we import `greetr`. 
This part might differ if you use a framework other than Flask, but you should in any case end up with an import named `application`, which is what Apache will be looking for.

### Configuring Apache

At last, we need to configure Apache itself, by adding a [virtualhost configuration](http://httpd.apache.org/docs/2.2/vhosts/) for Greetr.

The example project contains the configuration you need. 
Simply copy `greetr.vhost` to the Apache site configuration folder:

```bash
$ sudo cp greetr.vhost /etc/apache2/sites-available/greetr
```

The configuration looks like this:

```apache
<VirtualHost *:80>
    ServerName localhost
    ServerAlias localhost

    WSGIDaemonProcess greetr user=www-data group=www-data threads=5
    WSGIScriptAlias / /path/to/where/you/put/greetr/greetr.wsgi

    <Directory /path/to/where/you/put/greetr/>
        WSGIProcessGroup greetr
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>

    # Custom log file locations
    LogLevel warn
    ErrorLog  /path/to/where/you/put/greetr/error.log
    CustomLog /path/to/where/you/put/greetr/access.log combined
</VirtualHost>
```

The file tells Apache where to find the wsgi-file we wrote above, other details on how to start the WSGI deamon process, as well as on what domain it should serve the site.
Change the paths to wherever you placed the application, and the values of `ServerName` and `ServerAlias` if you are doing this on a remote server.

Next we need to activate the site:

```bash
$ sudo a2ensite greetr
```

The `a2ensite` command will simply symlink `greetr` from the `sites-available` directory and into `sites-enabled`, which is where Apache look for the activated virualhosts.
Once this is done, we need to restart Apache for the changes to take effect.

```bash
$ sudo service apache2 restart
```

*(Side note: some flavours of Apache differs from the one shipped with Ubuntu. If you have trouble finding the `sites-available` directory, you probably just need to put the virtualhost configuration directly inside `apache2.conf`.)*

And that's it, the application should now be working and running under Apache!
