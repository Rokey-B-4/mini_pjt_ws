from setuptools import find_packages, setup

package_name = 'mini_pjt_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rokey',
    maintainer_email='ts4955ts@gmail.com',
    description='Mission state machine and rc_car approach controller for TurtleBot4',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'mission_manager_node = mini_pjt_control.mission_manager_node:main',
            'target_seeker_node = mini_pjt_control.target_seeker_node:main',
            'car_approach_node = mini_pjt_control.car_approach_node:main',
            'approach_controller = mini_pjt_control.approach_controller:main',
        ],
    },
)
