import os

dirname = r'C:\Users\קובי\Documents\GitHub\RayCasting3D\Assets\Images\Textures\Mapped2'

for file in os.listdir(dirname):

    copy = file.replace('tile', '')
    copy = copy.replace('.png', '')

    os.rename(os.path.join(dirname, file), os.path.join(dirname, str(int(copy)) + '.png'))