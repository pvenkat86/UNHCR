import numpy as np
import pandas as pd
import logging
import sys
from PIL import Image
import os
import glob
import ntpath
from osgeo import gdal
import rasterio as rio
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import matplotlib as mpl
import geopandas as gpd
import earthpy as et
import earthpy.spatial as es
from rasterio.plot import show
import time
import numpy.ma as ma
import argparse


class Bands_to_RGB:
        def load_bands_list(self, directory):
            '''
            Loads all bands paths from one Landsat8 image to a list
            @return: list of paths
            '''
            image_dict = {}
            image_list = []
            for filename_path in glob.glob(directory + '*band*.tif'): 
                image_list.append(filename_path)
                filename = ntpath.basename(filename_path)            
                channel_name = filename.split(".")[0].split('_')[8]
                number = channel_name.replace("band", "")
                image_dict[number] = filename_path
                
            for filename_path in glob.glob(directory + '*B*.TIF'): 
                if 'QA' not in filename_path:
                    image_list.append(filename_path)
                    filename = ntpath.basename(filename_path)            
                    channel_name = filename.split(".")[0].split('_')[7]
                    number = channel_name.replace("B", "")
                    image_dict[int(number)] = filename_path
             
                
            new_image_list = []
            for key in sorted(image_dict.keys()) :
                new_image_list.append(image_dict[key])
                
                
            return new_image_list
        
        def create_stacked_image(self, HOME_DIR, stacked_file_output, paths_list):
            '''
            Generates stacked image from all bands
            void
            '''

            stack_data, metadata = es.stack(paths_list[:7] , HOME_DIR + stacked_file_output)
         
        def create_rgb_plots(self, HOME_DIR, plot_to_generate, stacked_file_output):
            with rio.open(HOME_DIR + stacked_file_output) as src:
                write_operation = src.read()                
                
                if plot_to_generate == '1' or plot_to_generate == 'all':
                    plot_rgb(write_operation,
                            rgb=[3, 2, 1],
                title="Natural Color", dest_file=HOME_DIR + "rgb_image_natural_color")

                if plot_to_generate == '2' or plot_to_generate == 'all':
                    plot_rgb(write_operation,
                            rgb=[4, 3, 2],
                title="Color Infrared (vegetation)", dest_file=HOME_DIR + "rgb_image_infrared")
        
                if plot_to_generate == '3' or plot_to_generate == 'all':
                    plot_rgb(write_operation,
                            rgb=[5, 4, 3],
                title="Vegetation Analysis", dest_file=HOME_DIR + "_" + "rgb_image_vegitation")
            
                if plot_to_generate == '4' or plot_to_generate == 'all':
                    '''
                    ndvi calculation, empty cells or nodata cells are reported as 0
                    '''
                    red = normalize(write_operation[3])
                    nir = normalize(write_operation[4])

                    np.seterr(divide='ignore', invalid='ignore')
                    ndvi = np.empty(src.shape, dtype=rio.float64)
                    
                    ndvi = np.where(
                        (nir + red) == 0.,
                        0,
                        (nir - red) / (nir + red))

                    ndviImage = rio.open(HOME_DIR + 'ndviImage.tiff', 'w', driver='Gtiff',
                          width=src.width,
                          height=src.height,
                          count=1, crs=src.crs,
                          transform=src.transform,
                          dtype='float64',
                          )
                    ndviImage.write(ndvi, 1)
                    ndviImage.close()
                    plt.imsave(HOME_DIR + 'ndvi_cmap.png', ndvi, cmap='Greens')
                    plt.close

                if plot_to_generate == '5' or plot_to_generate == 'all':
                        plot_rgb(write_operation,
                            rgb=[6, 5, 3],
                            title="False Color Urban", dest_file=HOME_DIR + "rgb_image_urban")
        
                if plot_to_generate == '6' or plot_to_generate == 'all':
                        plot_rgb(write_operation,
                            rgb=[5, 4, 1],
                            title="Agriculture", dest_file=HOME_DIR + "rgb_image_agriculture")
        
                if plot_to_generate == '7' or plot_to_generate == 'all':
                        plot_rgb(write_operation,
                            rgb=[6, 5, 4],
                            title="Atmospheric Penetration", dest_file=HOME_DIR + "rgb_image_atmospheric_penetration")
                
                if plot_to_generate == '8' or plot_to_generate == 'all':
                        plot_rgb(write_operation,
                            rgb=[4, 5, 1],
                            title="Healthy Vegitation", dest_file=HOME_DIR + "rgb_image_healthy_vegetation")
 
                if plot_to_generate == '9' or plot_to_generate == 'all':
                    '''
                    ndwi calculation, empty cells or nodata cells are reported as 0
                    '''
                    green = normalize(write_operation[2])
                    swir = normalize(write_operation[5])

                    np.seterr(divide='ignore', invalid='ignore')
                    ndvi = np.empty(src.shape, dtype=rio.float64)
                    
                    ndwi = np.where(
                        (swir + green) == 0.,
                        0,
                        (green - swir) / (green + swir))
                    ndwiImage = rio.open(HOME_DIR + 'ndwiImage.tiff', 'w', driver='Gtiff',
                          width=src.width,
                          height=src.height,
                          count=1, crs=src.crs,
                          transform=src.transform,
                          dtype='float64',
                          )
                    ndwiImage.write(ndwi, 1)
                    ndwiImage.close()
                    plt.imsave(HOME_DIR + 'ndwi_cmap.png', ndwi, cmap="Blues")
                    plt.close
      
                if plot_to_generate == '10' or plot_to_generate == 'all':
                        plot_rgb(write_operation,
                            rgb=[6, 4, 2],
                            title="Atmospheric Removal", dest_file=HOME_DIR + "rgb_image_atmospheric_removal")
                    
                if plot_to_generate == '11' or plot_to_generate == 'all':
                        plot_rgb(write_operation,
                            rgb=[6, 4, 3],
                            title="Short wave infrared", dest_file=HOME_DIR + "rgb_image_short_wave_infrared")
                  
                        
def normalize(array):
    array_min, array_max = array.min(), array.max()
    return ((array - array_min) / (array_max - array_min))


def plot_rgb(
    arr,
    rgb=(0, 1, 2),
    figsize=(10, 10),
    str_clip=2,
    ax=None,
    extent=None,
    title="",
    stretch=None,
    dest_file=None 
):
    if len(arr.shape) != 3:
        raise ValueError(
            "Input needs to be 3 dimensions and in rasterio "
            "order with bands first"
        )

    # Index bands for plotting and clean up data for matplotlib
    rgb_bands = arr[rgb, :, :]

    if stretch:
        rgb_bands = _stretch_im(rgb_bands, str_clip)

    # If type is masked array - add alpha channel for plotting
    if ma.is_masked(rgb_bands):
        # Build alpha channel
        mask = ~(np.ma.getmask(rgb_bands[0])) * 255

        # Add the mask to the array & swap the axes order from (bands,
        # rows, columns) to (rows, columns, bands) for plotting
        rgb_bands = np.vstack(
            (es.bytescale(rgb_bands), np.expand_dims(mask, axis=0))
        ).transpose([1, 2, 0])
    else:
        # Index bands for plotting and clean up data for matplotlib
        rgb_bands = es.bytescale(rgb_bands).transpose([1, 2, 0])

    # Then plot. Define ax if it's undefined
    show = False
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        show = True

    ax.imshow(rgb_bands, extent=extent)
    ax.set_title(title)
    ax.set(xticks=[], yticks=[])

    if show:
        plt.savefig(dest_file)
        plt.clf()
    return ax

parser = argparse.ArgumentParser(description='Generate RGB images')
parser.add_argument('homeDir', metavar='homeDir', type=str,
                    help='Directory to load files to/from')
parser.add_argument('stckof', metavar='stckof', type=str,
                    help='Path to stacked image output file.')
parser.add_argument('ptg', metavar='ptg', type=str,
                    help='Plots to generate. 1 - Natural Color Image, 2- Color Infrared, 3- Vegitation Analysis')

args = parser.parse_args()


bands_to_rgb = Bands_to_RGB() 
paths_list = bands_to_rgb.load_bands_list(args.homeDir)
bands_to_rgb.create_stacked_image(args.homeDir, args.stckof, paths_list)
bands_to_rgb.create_rgb_plots(args.homeDir, args.ptg, args.stckof)
