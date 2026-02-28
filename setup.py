import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="endstone-easyluckypillar",
    version="0.1.2",
    author="MengHanLOVE",
    url='https://github.com/MengHanLOVE1027',
    author_email="2193438288@qq.com",
    description="一个基于 EndStone 的幸运之柱小游戏插件 / A Lucky Pillar mini-game plugin based on EndStone.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
)
