import os
import pandas as pd
import cv2
from joint import Joint
from pose import Pose
from tqdm import tqdm
import argparse

def get_coords_of_frame_nos(cam_coords_path,frame_no,frame_no_count=10):
    frame_coords_chunks = []
    for index, cam_coords_chunk in enumerate(pd.read_csv(cam_coords_path, chunksize=10 ** 8)):
        frame_coords_chunk = cam_coords_chunk[(cam_coords_chunk["frame_no_cam"] >= frame_no) & (cam_coords_chunk["frame_no_cam"] < frame_no + frame_no_count)]
        if len(frame_coords_chunk) > 0:
            frame_coords_chunks.append(frame_coords_chunk)

    frame_coords = pd.concat(frame_coords_chunks)
    return frame_coords

def get_joints_from_person_coords(coords_one_person_frame):

    coords_one_person_frame = coords_one_person_frame[['frame_no_cam'
                                                        ,'person_id'
                                                        ,'joint_type'
                                                        , 'x_2D_joint'
                                                        , 'y_2D_joint'
                                                        , 'x_3D_joint'
                                                        , 'y_3D_joint'
                                                        , 'z_3D_joint'
                                                        , 'joint_occluded'
                                                        , 'joint_self_occluded'
                                                        , 'x_top_left_BB'
                                                        , 'y_top_left_BB'
                                                        , 'x_bottom_right_BB'
                                                        , 'y_bottom_right_BB'
                                                        , 'x_2D_person'
                                                        , 'y_2D_person'
                                                        , 'wears_glasses'
                                                        , 'ped_type']]
    person_joints = []
    for person_joint_coords in coords_one_person_frame.values.tolist():
        person_joint = Joint(person_joint_coords)
        person_joints.append(person_joint)

    return person_joints

def draw_annotations(coords_folder,video_folder,output_folder,cam_ids):

    for cam_id in cam_ids:
        cam_coords_path = os.path.join(coords_folder, "cam_{}".format(cam_id), "coords_cam_{}.csv".format(cam_id))
        cam_video_path = os.path.join(video_folder, "cam_{}".format(cam_id), "cam_{}.mp4".format(cam_id))

        print("Loading {}".format(cam_video_path))

        cam_video_output_folder = os.path.join(output_folder, "cam_{}".format(cam_id))
        os.makedirs(cam_video_output_folder,exist_ok=True)
        output_cam_video_path = os.path.join(cam_video_output_folder, "annotations_cam_{}.mp4".format(cam_id))

        print("Writing {}".format(output_cam_video_path))

        cam_coords = pd.read_csv(cam_coords_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        out = cv2.VideoWriter(output_cam_video_path, fourcc, 41.0, (1920, 1080))


        #Get frames until the video ends
        cam_video_capture= cv2.VideoCapture(cam_video_path)
        total_frames = int(cam_video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        tqdm_progress = tqdm(total=total_frames)

        current_frame_no = 0

        while True:
            ret, frame = cam_video_capture.read()
            tqdm_progress.update()
            coords_frame = cam_coords[cam_coords["frame_no_cam"] == current_frame_no]
            for person_id in list(coords_frame["person_id"]):
                coords_one_person_frame = coords_frame[coords_frame["person_id"] == person_id]
                person_joints = get_joints_from_person_coords(coords_one_person_frame)
                pose = Pose(person_joints)
                pose.drawBoundingBox(image=frame,color=(255,0,0))
                pose.drawPersonId(image=frame)
                pose.drawPose(image=frame,color=[0,255,0])


            if not ret:
                out.release()
                cam_video_capture.release()
                break

            cv2.imshow("",mat=frame)
            cv2.waitKey(1)

            out.write(image=frame)



            current_frame_no += 1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coords_folder", type=str,default="/media/philipp/philippkoehl_ssd/MTA_ext_short_coords/test")
    parser.add_argument("--video_folder", type=str,default="/media/philipp/philippkoehl_ssd/MTA_ext_short/test")
    parser.add_argument("--output_folder", type=str,default="/media/philipp/philippkoehl_ssd/MTA_ext_short_annotation_videos")
    parser.add_argument("--camera_ids", type=str, default="0,1,2,3,4,5")

    args = parser.parse_args()
    args.camera_ids = list(map(int,args.camera_ids.split(",")))
    return args


def main():
    args = parse_args()
    draw_annotations(coords_folder=args.coords_folder
                     ,video_folder=args.video_folder
                     ,output_folder=args.output_folder
                     ,cam_ids=args.camera_ids)


if __name__ == "__main__":
    main()