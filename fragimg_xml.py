# -*- coding: utf-8 -*-
'''
export fragment image bounding boxes:
1>  read physical xml
2>  export fragment image bounding boxes in pixel units to xml file
'''

import sys
import os
import numpy as np
import argparse
import itertools
import xml.dom.minidom
import cv2
from PIL import Image

# add marmot to python path
path = os.path.abspath(__file__)
for i in range(4):
    path = os.path.dirname(path)
sys.path.insert(0, path)

from marmot.common.label import *
from marmot.brain.feature.context import Context
from marmot.common.raw.document import Document as RawDoc
from marmot.common.physical.document import Document as PhysicalDoc
from marmot.brain.util import label_encoder


DOC_PALETTE = np.asarray([
    (255, 255, 0),
    (244, 35, 232),   
    (102, 102, 156),
    (190, 153, 153),
    (153, 153, 153),
    (250, 170, 30),
    (220, 220, 0),
    (107, 142, 35),
    (152, 251, 152),
    (70, 130, 180),
    (220, 20, 60),
    (255, 0, 0),
    (0, 0, 142),
    (0, 80, 100),
    (0, 0, 230),
    (119, 11, 32),
    (0, 0, 0)], dtype=np.uint8)

def create_element(dom, frag_box, object, ele_name):
    element = dom.createElement(ele_name)
    value = dom.createTextNode(frag_box)
    element.appendChild(value)
    object.appendChild(element)
    return dom, object

def generate_xml(frag_boxes):
    impl = xml.dom.minidom.getDOMImplementation()
    dom = impl.createDocument(None, 'annotation', None)
    root = dom.documentElement

    for f in frag_boxes:
        object = dom.createElement('object')
        root.appendChild(object)
        
        dom, object = create_element(dom, f[1], object, 'logical_label')
        box = dom.createElement('box')
        object.appendChild(box)
       
        dom, object = create_element(dom, str(f[0].x0), box, 'xmin')
        dom, object = create_element(dom, str(f[0].x1), box, 'xmax')
        dom, object = create_element(dom, str(f[0].y0), box, 'ymin')
        dom, object = create_element(dom, str(f[0].y1), box, 'ymax')        
    return dom

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='export fragment image bounding boxe.')
    parser.add_argument('target',
                        help='index of sample data names and pages.')
    args = parser.parse_args()

    dir = os.path.dirname(args.target)
    with open(args.target) as f:
        for line in f:
            # split line into document name and page numbers
            name, page_nums = line.split(':')
            page_nums = [int(page_num) for page_num in page_nums.split()]
            print 'processing: %s' % name

            # read document
            raw_doc = RawDoc.from_index_xml(
                os.path.join(dir, name, 'raw', 'index.xml'))
            physical_doc = PhysicalDoc.from_index_xml(
                raw_doc, os.path.join(dir, name, 'physical', 'index.xml'))
           
            # handle each target page
            for page_num in page_nums:
                page = physical_doc[page_num]
                img_path = os.path.join(dir, name, 'raw', str(page_num) + '.png')
                map_path = os.path.join(dir, 'gt2', name + '-'+ str(page_num) + '.png')
                xml_path = os.path.join(dir, 'gt2', name + '-'+ str(page_num) + '.xml')
                orig_path = os.path.join(dir, 'gt3', name + '-'+ str(page_num) + '.png')

                orig = Image.open(img_path)
                orig.save(orig_path)

                # generate grouth truth image
                context = Context(page, img_path)
                f_boxes = context.frag_img
                image = Image.open(img_path).convert('L')
                map_img = Image.new('L', image.size)
                map_img.paste(255)               
                for f in f_boxes:
                    bbox = (int(f[0].x0), int(f[0].y0), int(f[0].x1), int(f[0].y1))
                    color = label_encoder.transform([f[1]])                
                    map_img.paste(color, bbox)                
                map_img.save(map_path)
                
                # generate grouth truth xml
                f_boxes = context.frag_img                
                f_dom = generate_xml(f_boxes)
                f_xml = open(xml_path, 'w')
                f_dom.writexml(f_xml, addindent = ' ', newl = '\n')           
                f_xml.close()
                
               


