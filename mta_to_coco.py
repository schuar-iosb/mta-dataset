import os.path as osp
import numpy as np
import pandas as pd
import os
import cv2
from tqdm import tqdm
import json
import argparse


def constrain_bbox_to_img_dims(xyxy_bbox,img_dims=(1920,1080)):
    img_width, img_height = img_dims
    xtl_res, ytl_res, xbr_res, ybr_res = xyxy_bbox

    if xtl_res < 0: xtl_res = 0

    if xtl_res >= img_width: xtl_res = img_width  # should not occur

    if ytl_res < 0: ytl_res = 0

    if ytl_res >= img_height: ytl_res = img_height

    if xbr_res < 0: xbr_res = 0

    if xbr_res >= img_width: xbr_res = img_width

    if ybr_res < 0: ybr_res = 0

    if ybr_res >= img_height: ybr_res = img_height

    return [xtl_res, ytl_res,xbr_res,ybr_res]





def get_frame_annotation(cam_coords_frame: pd.DataFrame, image_id: int, image_size: tuple,annotation_id:int):


    annotations = []

    for idx,ped_row in cam_coords_frame.iterrows():



        bbox = [
            int(ped_row["x_top_left_BB"]),
            int(ped_row["y_top_left_BB"]),
            int(ped_row["x_bottom_right_BB"]),
            int(ped_row["y_bottom_right_BB"])
        ]
        bbox = constrain_bbox_to_img_dims(bbox)

        #bbox is [x,y,width,height]
        bbox = xyxy2xywh(np.asarray(bbox))

        width = bbox[2]
        height = bbox[3]

        area = float(width * height)



        annotation = {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": 1,
            "iscrowd": 0,
            "area": area,
            "bbox": bbox,
            "width": image_size[0],
            "height": image_size[1],
        }

        annotations.append(annotation)
        annotation_id += 1




    return annotation_id,annotations



def convert_annotations(mta_dataset_path, coco_mta_dataset_path, sampling_rate, camera_ids, img_dims=(1920, 1080), person_id_name="person_id"):

    coco_dict = {
        'info': {
            'description': 'MTA',
            'url': 'mta.',
            'version': '1.0',
            'year': 2020,
            'contributor': 'Philipp Koehl',
            'date_created': '2019/07/16',
        },
        'licences': [{
            'url': 'http://creativecommons.org/licenses/by-nc/2.0',
            'id': 2,
            'name': 'Attribution-NonCommercial License'
        }],
        'images': [],
        'annotations': [],
        'categories': [{
                           'supercategory':'person',
                           'id':1,
                           'name':'person'
                        },
                        {
                            'supercategory': 'background',
                            'id': 2,
                            'name': 'background'
                        }
                        ]
    }

    coco_gta_dataset_images_path = osp.join(coco_mta_dataset_path, "images")
    os.makedirs(coco_gta_dataset_images_path,exist_ok=True)
    current_annotation_id = 0
    current_image_id = 0

    for cam_id in camera_ids:
        print("processing cam_{}".format(cam_id))

        cam_path = os.path.join(mta_dataset_path,"cam_{}".format(cam_id))
        csv_path = osp.join(cam_path, "coords_fib_cam_{}.csv".format(cam_id))
        video_path = osp.join(cam_path, "cam_{}.mp4".format(cam_id))

        cam_coords = pd.read_csv(csv_path)
        video_capture = cv2.VideoCapture(video_path)

        frame_nos_cam = list(set(cam_coords["frame_no_cam"]))
        frame_nos_cam = frame_nos_cam[0::sampling_rate]

        pbar = tqdm(total=len(frame_nos_cam))

        def updateTqdm(*a):
            pbar.update()

        for frame_no_cam in frame_nos_cam:
            updateTqdm()

            cam_coords_frame = cam_coords[cam_coords["frame_no_cam"] == frame_no_cam ]


            current_annotation_id,frame_annotations = get_frame_annotation(cam_coords_frame=cam_coords_frame,image_id=current_image_id,image_size=img_dims,annotation_id=current_annotation_id)
            image_name = "imageid_{}.jpg".format(current_image_id)
            image_path_gta_coco = osp.join(coco_gta_dataset_images_path,image_name)


            coco_dict['images'].append({
                'license': 4,
                'file_name': image_name,
                'height': img_dims[1],
                'width': img_dims[0],
                'date_captured': '2019-07-28 00:00:00',
                'id': current_image_id
            })

            coco_dict['annotations'].extend(frame_annotations)

            video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_no_cam)

            ret, frame = video_capture.read()
            if ret:
                cv2.imwrite(filename=image_path_gta_coco,img=frame)

            current_image_id += 1

    with open(osp.join(coco_mta_dataset_path, "coords.json"), 'w') as fp:
        json.dump(coco_dict,fp=fp,sort_keys=True,indent=3)

    return coco_dict


def xyxy2xywh(bbox):
    _bbox = bbox.tolist()
    return [
        _bbox[0],
        _bbox[1],
        _bbox[2] - _bbox[0] + 1,
        _bbox[3] - _bbox[1] + 1,
    ]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mta_dataset_folder", type=str,default="/media/philipp/philippkoehl_ssd/MTA_ext_short/test")
    parser.add_argument("--coco_mta_output_folder", type=str,default="/media/philipp/philippkoehl_ssd/coco_MTA_ext_short/test")
    parser.add_argument("--sampling_rate", type=int,default=41)
    parser.add_argument("--camera_ids", type=str, default="0,1,2,3,4,5")

    args = parser.parse_args()
    args.camera_ids = list(map(int,args.camera_ids.split(",")))
    return args

def main():

    args = parse_args()
    convert_annotations(mta_dataset_path=args.mta_dataset_folder
                        , coco_mta_dataset_path=args.coco_mta_output_folder
                        ,sampling_rate=args.sampling_rate
                        ,camera_ids=args.camera_ids)



if __name__ == '__main__':
    main()
