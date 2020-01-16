from bfio.bfio import BioReader, BioWriter
import bioformats
import javabridge as jutil
import argparse, logging, imagesize, re, difflib
import numpy as np
from pathlib import Path

def get_coords(imgName):
    regex = "x([0-9]+)_y([0-9]+).ome.tif"
    groups = re.match(regex,imgName).groups()
    X = groups[0]
    Y = groups[1]

    return X,Y

if __name__=="__main__":

    # Setup the argument parsing
    parser = argparse.ArgumentParser(prog='assemble', description='Assemble images from a single stitching vector.')
    parser.add_argument('--imgPath', dest='imgPath', type=str,
                        help='Input image tiles', required=True)
    parser.add_argument('--outFile', dest='outFile', type=str,
                        help='Path to and name of output file', required=True)
    parser.add_argument('--refImg', dest='refImg', type=str,
                        help='Path to one original file', required=True)
    parser.add_argument('--width', dest='width', type=str,
                        help='Width of the output image', required=True)
    parser.add_argument('--height', dest='height', type=str,
                        help='Height of the output image', required=True)


    # Parse the arguments
    args = parser.parse_args()
    imgPath = args.imgPath
    outFile = args.outFile
    refImg = args.refImg
    width = int(args.width)
    height = int(args.height)

    # Initialize the logger
    logging.basicConfig(format='%(asctime)s - %(name)-8s - {} - %(levelname)-8s - %(message)s'.format(Path(outFile).name),
                        datefmt='%d-%b-%y %H:%M:%S')
    logger = logging.getLogger("assemble")
    logger.setLevel(logging.INFO)

    # Start the javabridge with proper java logging
    logger.info('Starting the javabridge...')
    log_config = Path(__file__).parent.joinpath("log4j.properties")
    jutil.start_vm(args=["-Dlog4j.configuration=file:{}".format(str(log_config.absolute()))],class_path=bioformats.JARS)

    # Get a list of all images to be merged
    images = [f for f in Path(imgPath).iterdir() if ''.join(f.suffixes)=='.ome.tif']
    images.sort()
    
    # Initialize the output file
    br = BioReader(str(Path(refImg).absolute()))
    bw = BioWriter(str(Path(outFile).absolute()),metadata=br.read_metadata())
    bw.num_x(width)
    bw.num_y(height)
    del br

    for ind,img in enumerate(images):
        logger.info('{:.2f}% complete...'.format(100*ind/len(images)))
        br = BioReader(str(img.absolute()))
        X,Y = get_coords(img.name)
        for x in range(0,br.num_x(),1024):
            for y in range(0,br.num_y(),1024):
                image = br.read_image(X=[x,min(x+1024,br.num_x())],Y=[y,min(y+1024,br.num_y())])
                bw.write_image(image,X=[int(X)+x],Y=[int(Y)+y])
        img.unlink()
        del br
    logger.info('100% complete...')
    
    bw.close_image()

    jutil.kill_vm()
    