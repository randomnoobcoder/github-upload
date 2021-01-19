#!/usr/bin/env python3
import io
from multiprocessing import Pool
from google.cloud import videointelligence
from google.cloud.videointelligence import enums, types
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key.json'  # 'C:\\Codelab\\shot-change-detection-master\\keys.json'
# video_uri = 'C:\\Codelab\\shot-change-detection-master\\data\\testvideo.mp4'
# video1 = 'gs://shot-change-detection/cctv_test.mp4'
# video1 = 'C:\\Codelab\\shot-change-detection-master\\data\\cctv_test.mp4'
# video2 = 'C:\\Codelab\\shot-change-detection-master\\data\\testvideo.mp4'
video1 = 'data\\vid1.mp4'
video2 = 'data\\vid2.mp4'
inputs = [video1, video2]


def object_detection(video_uri):
    video_client = videointelligence.VideoIntelligenceServiceClient()

    feature = [enums.Feature.OBJECT_TRACKING]
    with io.open(video_uri, 'rb') as file:
        input_content = file.read()

    operation = video_client.annotate_video(
        input_content=input_content,
        features=feature)
    print("\nProcessing video {} ....".format(video_uri))

    result = operation.result(timeout=500)

    object_annotations = result.annotation_results[0].object_annotations
    object_list = []
    for annotation in object_annotations:
        entity = annotation.entity
        description = entity.description
        object_list.append(description)
        entity_id = entity.entity_id
        confidence = annotation.confidence
        start_ms = annotation.segment.start_time_offset.ToMilliseconds()
        end_ms = annotation.segment.end_time_offset.ToMilliseconds()
        # print(f'{description:<22}',
        #       f'{entity_id:<10}',
        #       f'{confidence:4.0%}',
        #       f'{start_ms:>7}',
        #       f'{end_ms:>7}',
        #       sep=' | ')
    #print("Objects found in {} :: {}".format(video_uri, set(object_list)))
    return object_list


if __name__ == "__main__":
    p = Pool(len(inputs))
    output = p.map(object_detection, inputs)
    objects_list_video1 = output[0]
    objects_list_video2 = output[1]

    # print(objects_list_video1)
    # print(objects_list_video2)
    missing_items = []
    for item in objects_list_video1:
        if item not in objects_list_video2:
            missing_items.append(item)
    print('Missing Items are : {}'.format(set(missing_items)))
