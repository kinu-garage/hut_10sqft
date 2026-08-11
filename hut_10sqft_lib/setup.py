from setuptools import find_packages, setup

package_name = 'hut_10sqft_lib'

setup(
 name=package_name,
 version='0.4.0',
 packages=[package_name],
 data_files=[
     ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
     ('share/' + package_name, ['package.xml']),
   ],
 install_requires=[
     'colcon-common-extensions',
     'setuptools',
     ],
 zip_safe=True,
 maintainer='Isaac Saito',
 maintainer_email='iisaac.saito@gmail.com',
 description='A library package for generic utility for setting up computer environment.',
 license='Apache',
 entry_points={},
 extras_require={
  'test': ['pytest'],
 },
)
