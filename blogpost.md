Serving Python Webapps With Apache
===

Python is a great language that is useful for many things, among them creating web applications.
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

The first things we will need to install are couple of tools that are handy when doing Python development: [pip](http://www.pip-installer.org/en/latest/) and [virtualenv](http://www.virtualenv.org/en/latest/).
If you are already familiar with these, and know how to use them, skip ahead to the next section.

```bash
$ sudo apt-get install python-pip
$ sudo apt-get install python-virtualenv
$ sudo apt-get install virtualenvwrapper
```

`pip` is a package manager for Python.
`virtualenv` is a tool for creating small virtual environments where we can install Python packages, and [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) is simply a set of tools to make it easier to work with virtual environments.
Once you have these installed open a fresh terminal, which will force `virtualenvwrapper` to do some initial setup.

With newer versions of `virtualenvwrapper` this is all that is needed.
Should you be using an older version, for example the default one under Ubuntu 12.04, you might also want to add the following lines to your`~/.bashrc` file:

```bash
export WORKON_HOME=~/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```

And run this command:

```bash
$ mkdir ~/.virtualenvs
```

Next, let's move on to have a look at [Greetr](https://github.com/kvalle/greetr), the example application we'll be installing as part of this tutorial.

### The Example

To have a concrete example to work with, I created a simple example application.
It is called Greetr, and is little more than a glorified "Hello World".
It is, however, a working Python web app, written within the [Flask framework](http://flask.pocoo.org/).

If your preferred Python web framework is something other than Flask, such as [Pyramid](http://www.pylonsproject.org/), [web2py](http://www.web2py.com/), [Django](https://www.djangoproject.com/), or any other, don't worry.
Chances are it too, like Flask, support the common standard for interfacing web servers and Python apps known as [WSGI](http://wsgi.readthedocs.org/en/latest/), the *Web Server Gateway Interface*, and the configuration should be similar to what we'll do here.

Now, if you like, check out [the Greetr applicaton](https://github.com/kvalle/greetr).
It is a small application, simply showing a picture of a smiling robot along with a random greeting.
The main point is for it to serve as a basis for the examples in this tutorial, and to give you something to verify the setup after completing the tutorial.

Let's start by cloning the sample application down from GitHub, and put it under `~/web/greetr`.

```bash
$ mkdir ~/web
$ git clone git://github.com/kvalle/greetr.git ~/web/greetr
$ cd ~/web/greetr
```

The next thing we need to do is to create a virtual environment.
We'll simply tell `virtualenv` to create one for us, and that it should be named `greetr`.

```bash
$ mkvirtualenv greetr
```

Now we have a fresh virtual Python environment where we can install anything, without worrying what other libraries (or in which versions) other applications install in their environments.
The prompt should have changed to indicate that we are currently working in the `greetr` environment.
You leave the virtual environment by using the command `deactivate`, and re-enter it by calling `workon greetr`.

Next we'll need to install the dependencies.
Greetr comes with the file [requirements.txt](https://github.com/kvalle/greetr/blob/master/requirements.txt), which lists everything you need to install.
Use `pip` to install the dependencies by issuing the following command:

```bash
$ pip install -r requirements.txt
```

Before we move on to installing and configuring Apache, lets check that everything is working.
Start Flask's embedded webserver using the provided script:

```bash
$ ./runserver.py
```

Then visit Greetr at [http://127.0.0.1:5000/](http://127.0.0.1:5000/). The app should now be working, so lets move on to see how we can start serving it using Apache.

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
This file contains everything necessary for Apaches `mod_wsgi` to instantiate and serve the application.

This is what [greetr.wsgi](https://github.com/kvalle/greetr/blob/master/greetr.wsgi) looks like:

```python
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
```

So, what happens here?

The first thing we do is to add another "site directory" for Python to use.
This is the directory where we have installed all of Greetr's dependencies under virtualenv.
We need to add this as a site directory explicitly because Apache won't know to use the `greetr` environment.
Also notice that the directory is somewhere under your home folder, so make sure you change `your-user` with whatever your username happens to be.

Secondly, we add the location of `greetr` to Pythons system path.
We need to do this in order to be able to import the `greetr` modules, both from the wsgi-file, aswell as from within `greetr` itself.

Finally we import `greetr`. 
This part might differ if you use a framework other than Flask, but you should in any case end up with an import named `application`, which is what Apache will be looking for.

### Configuring Apache

At last, we need to configure Apache itself, by adding a [virtualhost configuration](http://httpd.apache.org/docs/2.2/vhosts/) for Greetr.

The example project contains the configuration you need. 
Simply copy [greetr.vhost](https://github.com/kvalle/greetr/blob/master/greetr.vhost) to the Apache site configuration folder:

```bash
$ sudo cp greetr.vhost /etc/apache2/sites-available/greetr
```

The configuration looks like this:

```apache
<VirtualHost *:80>
    ServerName localhost
    ServerAlias localhost

    WSGIDaemonProcess greetr user=www-data group=www-data threads=5
    WSGIScriptAlias / /home/your-user/web/greetr/greetr.wsgi

    <Directory /home/your-user/web/greetr/>
        WSGIProcessGroup greetr
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>

    # Custom log file locations
    LogLevel warn
    ErrorLog  /home/your-user/web/greetr/error.log
    CustomLog /home/your-user/web/greetr/access.log combined
</VirtualHost>
```

Make sure you replace the `your-user` with the name ouf your user all four places.

The file tells Apache where to find the wsgi-file we wrote above, other details on how to start the WSGI deamon process, as well as on what domain it should serve the site.
Correct the paths to where we placed the application, and change the values of `ServerName` and `ServerAlias` if you are doing this on a remote server.

Next we need to activate the new `greetr` site, and disable the default one.:

```bash
$ sudo a2ensite greetr
$ sudo a2dissite default
```

The `a2ensite` command will simply symlink `greetr` from the `sites-available` directory and into `sites-enabled`, which is where Apache look for the activated virualhosts.
Once this is done, we need to reload the Apache configuration for the changes to take effect.

```bash
$ sudo service apache2 reload
```

*(Side note: some flavours of Apache differs from the one shipped with Ubuntu. If you have trouble finding the `sites-available` directory, you probably just need to put the virtualhost configuration directly inside `apache2.conf`.)*

And that's it, the application should now be working and running under Apache!
