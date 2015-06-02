import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-macros',
    version='0.4.0',
    packages=['macros', 'macros.templatetags'],
    include_package_data=True,
    install_requires='django >= 1.6',
    license='MIT License',
    description='A Django template tag library for repeating blocks tags and creating in template macros.',
    long_description=README,
    maintainer="Nick Lourie",
    maintainer_email="developer.nick@kozbox.com",
    keywords = "django repeat macros macro templatetags",
    url='https://github.com/nalourie/django-macros',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)

