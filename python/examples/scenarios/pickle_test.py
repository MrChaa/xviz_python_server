#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File: pickle_test.py
@Description: This module provides vehicle-colleted data live stream
@Date: 2022/11/8
@Author: zrf
@version: 1.0
"""
import time
import xviz_avs
import os
import numpy as np
import cv2
import pickle
import io as pyio
import time
from PIL import Image
from xviz_avs.builder import XVIZUIBuilder

class PickleScenario:
    def __init__(self,live=True, radius=30, duration=30, speed=10,pickle_folder='D:\项目\数据标注平台\平台原型开发\场景提取模块\数据demo') -> None:
        self._timestamp = time.time()
        self._radius = radius
        self._duration = duration
        self._speed = speed
        self._live = live
        self._metadata = None
        self._pickle_folder = pickle_folder
        self._file_list = []
        self._parse_folder()
        
    def get_metadata(self):
        if not self._metadata:
            builder = xviz_avs.XVIZMetadataBuilder()
            #*UI
            ui_builder = XVIZUIBuilder()
            p = ui_builder.panel('Camera')
            p.child(ui_builder.video(["/camera/image_00"]))
            ui_builder.child(p)
            builder.ui(ui_builder)
            #* ego vehicle
            builder.stream("/vehicle_pose").category(xviz_avs.CATEGORY.POSE)
            builder.stream("/vehicle/acceleration")\
            .category(xviz_avs.CATEGORY.TIME_SERIES)\
            .type(xviz_avs.SCALAR_TYPE.FLOAT)\
            .unit('m/s^2')
             #* objects
            builder.stream("/tracklets/objects")\
                .category(xviz_avs.CATEGORY.PRIMITIVE)\
                .type(xviz_avs.PRIMITIVE_TYPES.POLYGON)\
                .coordinate(xviz_avs.COORDINATE_TYPES.IDENTITY)\
                .stream_style({
                    'extruded': True,
                    'fill_color': [0, 200, 70, 128],
                })\
                .style_class('Car', {
                    'fill_color': [91, 145, 244, 64],
                    'stroke_color': [91, 145, 244, 64],
                })\
                .style_class('Pedestrian', {
                    'fill_color': [255, 198, 175, 64],
                    'stroke_color': [255, 198, 175, 128],
                })\
                .style_class('Bicycle', {
                    'fill_color': [149, 127, 206, 64],
                    'stroke_color': [149, 127, 206, 128],
                })\
                .style_class('Motorcycle', {
                    'fill_color': [149, 127, 206, 64],
                    'stroke_color': [149, 127, 206, 128],
                })\
                .style_class('Van', {
                    'fill_color': [0, 158, 0, 64],
                    'stroke_color': [0, 158, 0, 128]
                })\
                .style_class('Truck', {
                    'fill_color': [0, 158, 0, 64],
                    'stroke_color': [0, 158, 0, 128]
                })\
                .style_class('Bus', {
                    'fill_color': [158, 158, 0, 64],
                    'stroke_color': [158, 158, 0, 128]
                })\
                .style_class('Unknown', {
                    'fill_color': [255, 0, 0, 64],
                    'stroke_color': [255, 0, 0, 128]
                })
            #* lidar
            builder.stream("/lidar/points")\
                .category(xviz_avs.CATEGORY.PRIMITIVE)\
                .type(xviz_avs.PRIMITIVE_TYPES.POINT)\
                .stream_style({
                    'fill_color': [220, 220, 255, 64],
                    'radius_pixels': 1,
                })\
                .coordinate(xviz_avs.COORDINATE_TYPES.VEHICLE_RELATIVE)
            #* images
            builder.stream("/camera/image_00")\
                .category(xviz_avs.CATEGORY.PRIMITIVE)\
                .type(xviz_avs.PRIMITIVE_TYPES.IMAGE)
            if not self._live:
                log_start_time = self._timestamp
                builder.start_time(log_start_time)\
                    .end_time(log_start_time + self._duration)
            self._metadata = builder.get_message()
        if self._live:
            return {
                'type': 'xviz/metadata',
                'data': self._metadata.to_object()
            }
        else: return self._metadata
            
    def _parse_pickle(self,file_name):
        f = open(file_name, 'rb')
        data_dict = pickle.loads(f.read())
        for name, img in data_dict['image'].items():
            data_dict['image'][name] = cv2.imdecode(
                np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)
        return data_dict

    
    def _parse_folder(self):
        for root, dirs, files_name in os.walk(self._pickle_folder):
            for file_name in files_name:
                self._file_list.append(os.path.join(root, file_name))
    
    def get_message(self,timestamp):
        builder = xviz_avs.XVIZBuilder(metadata=self._metadata)
        self._draw_pose(builder,timestamp)
        self._draw_points(builder,timestamp)
        self._draw_camera(builder,timestamp)
        data = builder.get_message()
        if self._live:
            return {
                'type': 'xviz/state_update',
                'data': data.to_object()
            }
        else: return data
       
    def _draw_pose(self,builder,timestamp):
        builder.pose('/vehicle_pose').timestamp(timestamp).map_origin(
        0, 0, 0).orientation(0, 0, 0).position(0, 0, 0)
       
               
    def _draw_points(self,builder,timestamp):
        num = int(timestamp * 10)
        pickle_file = self._file_list[num]
        pkl = self._parse_pickle(pickle_file)
        lidar_points = pkl['points']['0-Ouster-OS1-128']
        positions = lidar_points[:,:3]
        builder.primitive('/lidar/points').points(positions.ravel())
        
    def _draw_camera(self,builder,timestamp):
        num = int(timestamp * 10)
        pickle_file = self._file_list[num]
        pkl = self._parse_pickle(pickle_file)
        image = pkl['image']['0']   
        img = Image.fromarray(image)
        w, h = img.width, img.height
        buf = pyio.BytesIO()
        img.save(buf, format='PNG')
        img_bytes = buf.getvalue()
        builder.primitive('/camera/image_00').image(img_bytes).dimensions(w,h)
        