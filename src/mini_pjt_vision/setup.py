from setuptools import find_packages, setup

package_name = 'mini_pjt_vision'

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
    description='Webcam trigger detector and TurtleBot4 OAK-D onboard detector (YOLO)',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'webcam_detector_node = mini_pjt_vision.webcam_detector_node:main',
            'robot_detector_node = mini_pjt_vision.robot_detector_node:main',
            'oakd_probe = mini_pjt_vision.oakd_probe:main',
        ],
    },
)
