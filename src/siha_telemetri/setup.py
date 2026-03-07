from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'siha_telemetri'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch dosyalarini tanitiyoruz
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ufukb',
    maintainer_email='ufukberkbayraktar@gmail.com',
    description='SIHA Telemetri Paketi',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'npc_publisher = siha_telemetri.npc_publisher:main',
        'gazebo_visualizer = siha_telemetri.gazebo_visualizer:main',
        'harita_node = siha_telemetri.harita_node:main',
        "npc_publisher2 = siha_telemetri.npc_publisher2:main",
    ],
    },
)