Serving Python Webapps With Apache
===

Python is a great language and useful for many things. 
Among them, and maybe especially, for writing web applications.
There is a [plethora of great web frameworks](http://wiki.python.org/moin/WebFrameworks) out there, and Python provdes a lot of useful modules for doing things such as [parsing json](http://docs.python.org/2/library/json.html) or [talking over HTTP](http://docs.python.org/2/library/httplib.html#module-httplib) out of the box.

If you don't need anyting fancy, Python even makes starting a simple HTTP server a one-liner from the command line:

	$ python -m SimpleHTTPServer
	Serving HTTP on 0.0.0.0 port 8000 ...

Once you come to production, however, you will generally require something more robust to serve your application.
In this blogpost I'll explain how to set up an [Apache HTTP Server](http://httpd.apache.org/) to serve Python web applications.

### Some Preliminary Setup

The steps of this tutorial will assume a setup of Ubuntu 12.10, with Apache 2.2 and Python 2.7 installed.
If you use a different configuration some details might differ, but the steps should still mostly be the same.

The first thing we will need is to install a couple of handy tools for working with Python development: [pip](http://www.pip-installer.org/en/latest/) and [virtualenv](http://www.virtualenv.org/en/latest/).
If you are already familiar with these, and know how to use them, skip ahead to the next section.

	$ sudo apt-get install python-virtualenv
	$ sudo apt-get install python-pip
	$ sudo apt-get install virtualenvwrapper

In addition we'll also want to add the following lines to our `~/.bashrc` file, to help virtualenvwrapper work it's magic:

	export WORKON_HOME=/path/to/your/python/environments
	source /usr/local/bin/virtualenvwrapper.sh

With the tools installed, we create a directory in which we will place our Python environment.
This should be the same directory we just specified in the `.bashrc` file.

	$ mkdir -p /path/to/your/python/environments

Next we simply tell `virtualenv` to create a new environment for us.

	$ mkvirtualenv greetr

Now we have a fresh virtual Python environment for our application, which we'll look at next.

### The Example

For purposes of this turtorial, I have created a simple example application.
It is called Greetr, and is little more than a glorified "Hello World".
It is, however, a working Python web app, written within the [Flask framework](http://flask.pocoo.org/).

If your preferred Python web framework is something other than Flask, such as [Pyramid](http://www.pylonsproject.org/), [web2py](http://www.web2py.com/), [Django](https://www.djangoproject.com/), or any other of the myriad of web frameworks for Python, don't worry.
Chances are it too supports the common standard for interfacing web servers and Python apps known as [WSGI](http://wsgi.readthedocs.org/en/latest/), the *Web Server Gateway Interface*, and the configuration should be similar.

Now, if you like, check out [the applicaton](https://github.com/kvalle/greetr).
It is a small application, simply showing a picture of a nice robot along with a random greeting.
Its details does not really matter, its main point is to serve as a basis for the examples in this tutorial, and to give you something to use to verify the setup after completing the tutorial.

Lets start by cloning the application down from GitHub so we have something to work with.

	$ git clone git://github.com/kvalle/greetr.git
	$ cd greetr

Next we'll need to install the dependencies.
First make sure you have the correct environment activated:

	$ workon greetr

Then use pip to install everything specified in [requirements.txt](https://github.com/kvalle/greetr/blob/master/requirements.txt).

	$ pip install -r requirements.txt

Before we move on to installing and configuring Apache, lets check that everything is working.
Start Flask's embedded webserver using the provided script `runserver.py`, then visit Greetr at [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

	$ ./runserver.py

The app should now be working, so lets move on to se how we can serve it using Apache.

### Install Apache

First, if you haven't already, install Apache along with the `mod_wsgi` module.

	$ sudo apt-get install apache2
	$ sudo apt-get install libapache2-mod-wsgi

Once installed, also make sure the module is activated, and that Apache is running.

	$ sudo a2enmod wsgi
	$ sudo service apache2 start


### The WSGI-file

The first thing we need to do to make Apache understand how to run our application is to write a `.wsgi` file.
This is the file we are going to tell Apache to run, and needs to contain everything necessary for Apaches `mod_wsgi` to instansiate the application.

Here is the [wsgi file](https://github.com/kvalle/greetr/blob/master/greetr.wsgi) we'll use for Greetr:

	import sys
	import site
	import os.path

	# Add custom site-packages directory
	your_env_package_dir = '/path/to/your/python/environments/greetr/lib/python2.7/site-packages'
	site.addsitedir(your_env_package_dir)

	# Add greetr to system path
	app_path = os.path.dirname(__file__)
	sys.path.insert(0, app_path)

	# Import greetr
	from greetr import app as application

So, what happens here?

First, since Apache won't be running the wsgi-file from within our nice and cozy custom made Python environment, we need to manually make the installed modules available.
We do this by specifying the path to our pyenv, and calling `site.addsitedir`.

Secondly, we add the location of `greetr` to Pythons system path.

Finally we import `greetr`. 
Note that we give it the name `application`, which is what Apache will be looking for.
This part will probably differ if you use a framework other than Flask.

### Configuring Apache

Finally, we need to configure Apache itself, by adding a virtualhosts configuration for Greetr.
The configuration should look something like this:

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

The file tells Apache where to find the wsgi-file we just wrote, and other details on how to start the WSGI deamon process.
Copy the file to place it among your other vhost files under Apache:

	$ sudo cp greetr.vhost /etc/apache2/sites-available/greetr

Next we need to activate the site:

	$ sudo a2ensite notato

The `a2ensite` command will simply symlink `greetr` from the `sites-available` directory and into `sites-enabled`.
Once this is done, we need to restart Apache for the changes to take effect.

	$ sudo service apache2 restart

*(Side note: some flavours of Apache differs from the one shipped with Ubuntu. If you have trouble finding the `sites-available` directory, you probably just need to put the virtualhost configuration directly inside `apache2.conf`.)*

And that's it, the application should now be working and running under Apache!
