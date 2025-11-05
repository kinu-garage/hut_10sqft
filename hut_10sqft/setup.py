import os
from setuptools import setup

exec_aptsrc = "apt-source_ros2.sh"
package_name = 'hut_10sqft'

setup(
    name=package_name,
    version='0.2.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),     
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'cmake',
        'colcon-common-extensions',
        'colcon-core',
        'hut_10sqft_lib',
        'setuptools'],
    zip_safe=True,
    maintainer='Isaac Saito',
    maintainer_email='iisaac.saito@gmail.com',
    description="A package primarilly for setting up the maintainers' personal computers environment.",
    license='Apache-2.0',
    scripts=[os.path.join("exec", exec_aptsrc)],
    entry_points={
        "console_scripts": [
        "suco = hut_10sqft.suco_main:main",
        "suco_installer = hut_10sqft.suco_installer:main"
        ]},
)
