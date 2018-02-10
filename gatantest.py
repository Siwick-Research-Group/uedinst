
from uedinst import GatanUltrascan895
import matplotlib.pyplot as plt

plt.switch_backend('Qt5Agg')

if __name__ == '__main__':

    with GatanUltrascan895() as camera:
        camera.insert(True)
        im = camera.acquire_image(1.0, antiblooming = True)
        print(im.dtype)
        plt.figure()
        plt.imshow(im)
        plt.show()