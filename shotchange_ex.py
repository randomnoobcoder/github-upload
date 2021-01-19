#!/usr/bin/env python3
import os

from google.cloud import videointelligence, storage
from google.cloud.videointelligence import enums
import cv2 as cv
import datetime
import urllib.request as req
from os import environ
import os
from google.cloud import storage
from google.oauth2 import service_account


def detect_shot_changes(video_uri):
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [enums.Feature.SHOT_CHANGE_DETECTION,
                enums.Feature.LABEL_DETECTION]
    print(f'Processing video "{video_uri}"...')
    operation = video_client.annotate_video(
        input_uri=video_uri,
        features=features,
    )
    return operation.result()


def video_shots(response):
    # First result only, as a single video is processed
    shots = response.annotation_results[0].shot_annotations
    print(shots)
    print(f' Video shots: {len(shots)} '.center(40, '-'))
    for i, shot in enumerate(shots):
        start_ms = shot.start_time_offset.ToMilliseconds()
        end_ms = shot.end_time_offset.ToMilliseconds()
        print(f'{i + 1:>3}',
              f'{start_ms:>7,}',
              f'{end_ms:>7,}',
              sep=' | ')
        print('Change detected..\nTaking Screenshot.... ')
        directory, captured_file = capture_frames(video, end_ms)
        print('Done')
        print("Uploading....")
        full_path = os.path.join(directory, captured_file)
        image_file = full_path.replace('\\', '/')
        upload_captured_image(bucket_name, image_file)


def generate_image_url(blob_path):
    """ generate signed URL of a video stored on google storage.
        Valid for 300 seconds in this case. You can increase this
        time as per your requirement.
    """
    blob = bucket.blob(blob_path)
    return blob.generate_signed_url(datetime.timedelta(minutes=5), method='GET')


def capture_frames(video_path, ms):
    url = generate_image_url(video_path)
    req.urlretrieve(url, video_path)
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f'Could not open video <{video_path}>')
    cap.set(cv.CAP_PROP_POS_MSEC, ms)
    ok, cv_frame = cap.read()
    if not ok:
        raise RuntimeError(f'Failed to get video frame @pos_ms[{ms}]')
    output_folder = 'Captured-Shots'
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    filename = 'shot_change_at_{}.jpg'.format(ms)
    cv.imwrite(os.path.join(output_folder, filename), cv_frame)
    return output_folder, filename


def upload_captured_image(bucket_name, filename):
    out_bucket = storage_client.get_bucket(bucket_name)
    blob = out_bucket.blob(filename)
    blob.upload_from_filename(filename)
    print('Uploaded file {} to bucket {} '.format(filename, bucket_name))


if __name__ == '__main__':
    #key_path = "D:\\CodeLab\\Projects\\shot-change-detection\\key.json"
    key_path='key.json'
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    # Explicitly use service account credentials by specifying the private key file.
    storage_client = storage.Client().from_service_account_json(key_path)
    # Make an authenticated API request
    bucket = storage_client.bucket('shot-change-detection')
    video_uri = 'gs://shot-change-detection/test.mp4'
    video = video_uri.split('/')[-1]
    bucket_name = "shot-change-detection"
    response = detect_shot_changes(video_uri)
    video_shots(response)
