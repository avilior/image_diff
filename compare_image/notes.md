# Installing numpy
Done from pycharm package manager

# Installing opencv

if open cv is installed on the host machine then we just need to sym link it into the virtual env


Use macports to install opencv for both python 2 and python 3 using the following command:

sudo port install opencv +python27 +python36


macports installs as follows:

/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/cv2.so
/opt/local/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/cv2.cpython-36m-darwin.so


Link the so into the virtualenv

cd /Users/avi/.virtualenvs/web/lib/python3.6/site-packages

create a link:

ln -s /opt/local/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/cv2.cpython-36m-darwin.so cv2.so





