__version__ = "2.0"

import collections
import struct
import json
import os

import numpy as np


# from https://github.com/colmap/colmap/blob/dev/scripts/python/read_write_model.py
CameraModel = collections.namedtuple(
    "CameraModel", ["model_id", "model_name", "num_params"])
Camera = collections.namedtuple(
    "Camera", ["id", "model", "width", "height", "params"])
BaseImage = collections.namedtuple(
    "Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])

def qvec2rotmat(qvec):
    # 将四元数转换为旋转矩阵
    return np.array([
        [1 - 2 * qvec[2]**2 - 2 * qvec[3]**2,
         2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3],
         2 * qvec[3] * qvec[1] + 2 * qvec[0] * qvec[2]],
        [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3],
         1 - 2 * qvec[1]**2 - 2 * qvec[3]**2,
         2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]],
        [2 * qvec[3] * qvec[1] - 2 * qvec[0] * qvec[2],
         2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1],
         1 - 2 * qvec[1]**2 - 2 * qvec[2]**2]])

class Image(BaseImage):
    def qvec2rotmat(self):
        return qvec2rotmat(self.qvec)

# 相机模型
CAMERA_MODELS = {
    CameraModel(model_id=0, model_name="SIMPLE_PINHOLE", num_params=3),
    CameraModel(model_id=1, model_name="PINHOLE", num_params=4),
    CameraModel(model_id=2, model_name="SIMPLE_RADIAL", num_params=4),
    CameraModel(model_id=3, model_name="RADIAL", num_params=5),
    CameraModel(model_id=4, model_name="OPENCV", num_params=8),
    CameraModel(model_id=5, model_name="OPENCV_FISHEYE", num_params=8),
    CameraModel(model_id=6, model_name="FULL_OPENCV", num_params=12),
    CameraModel(model_id=7, model_name="FOV", num_params=5),
    CameraModel(model_id=8, model_name="SIMPLE_RADIAL_FISHEYE", num_params=4),
    CameraModel(model_id=9, model_name="RADIAL_FISHEYE", num_params=5),
    CameraModel(model_id=10, model_name="THIN_PRISM_FISHEYE", num_params=12)
}
CAMERA_MODEL_IDS = dict([(camera_model.model_id, camera_model)
                         for camera_model in CAMERA_MODELS])
CAMERA_MODEL_NAMES = dict([(camera_model.model_name, camera_model)
                           for camera_model in CAMERA_MODELS])

# 读取二进制文件中的下一个字节
def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character="<"):
    """Read and unpack the next bytes from a binary file.
    :param fid:
    :param num_bytes: Sum of combination of {2, 4, 8}, e.g. 2, 6, 16, 30, etc.
    :param format_char_sequence: List of {c, e, f, d, h, H, i, I, l, L, q, Q}.
    :param endian_character: Any of {@, =, <, >, !}
    :return: Tuple of read and unpacked values.
    """
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)

# 读取二进制文件中的相机数据
def read_cameras_binary(path_to_model_file):
    """
    Read colmap camera binary format
    see: src/base/reconstruction.cc
        void Reconstruction::WriteCamerasBinary(const std::string& path)
        void Reconstruction::ReadCamerasBinary(const std::string& path)
    """
    cameras = {}
    with open(path_to_model_file, "rb") as fid:
        num_cameras = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_cameras):
            camera_properties = read_next_bytes(
                fid, num_bytes=24, format_char_sequence="iiQQ")
            camera_id = camera_properties[0]
            model_id = camera_properties[1]
            model_name = CAMERA_MODEL_IDS[camera_properties[1]].model_name
            width = camera_properties[2]
            height = camera_properties[3]
            num_params = CAMERA_MODEL_IDS[model_id].num_params
            params = read_next_bytes(fid, num_bytes=8*num_params,
                                     format_char_sequence="d"*num_params)
            cameras[camera_id] = Camera(id=camera_id,
                                        model=model_name,
                                        width=width,
                                        height=height,
                                        params=np.array(params))
        if len(cameras) != num_cameras:
            raise RuntimeError("Cameras dont match num_camera")
    return cameras

# 读取二进制文件中的images.bin
def read_images_binary(path_to_model_file):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadImagesBinary(const std::string& path)
        void Reconstruction::WriteImagesBinary(const std::string& path)
    """
    images = {}
    with open(path_to_model_file, "rb") as fid:
        num_reg_images = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_reg_images):
            binary_image_properties = read_next_bytes(
                fid, num_bytes=64, format_char_sequence="idddddddi")
            image_id = binary_image_properties[0]
            qvec = np.array(binary_image_properties[1:5])
            tvec = np.array(binary_image_properties[5:8])
            camera_id = binary_image_properties[8]
            image_name = ""
            current_char = read_next_bytes(fid, 1, "c")[0]
            while current_char != b"\x00":   # look for the ASCII 0 entry
                image_name += current_char.decode("utf-8")
                current_char = read_next_bytes(fid, 1, "c")[0]
            num_points2D = read_next_bytes(fid, num_bytes=8,
                                           format_char_sequence="Q")[0]
            x_y_id_s = read_next_bytes(fid, num_bytes=24*num_points2D,
                                       format_char_sequence="ddq"*num_points2D)
            xys = np.column_stack([tuple(map(float, x_y_id_s[0::3])),
                                   tuple(map(float, x_y_id_s[1::3]))])
            point3D_ids = np.array(tuple(map(int, x_y_id_s[2::3])))
            images[image_id] = Image(
                id=image_id, qvec=qvec, tvec=tvec,
                camera_id=camera_id, name=image_name,
                xys=xys, point3D_ids=point3D_ids)
    return images

# 将colmap的相机数据转换为meshroom的相机数据
def colmap2meshroom_instrinsics(logger, colmap_intrinsics, sfm_data={}):
    """
    Convert colmap's intrinsics data to meshroom's intrinsics data
    :param colmap_intrinsics: colmap's camera intrinsics
    :param sfm_data: meshroom's sfm data
    :return: Converted meshroom's sfm data
    """
    sfm_data = sfm_data.copy()
    intrinsics = []
    for camera_id, colmap_camera in colmap_intrinsics.items():
        intrinsic={
        "intrinsicId": camera_id,
        "width": colmap_camera.width,
        "height": colmap_camera.height,
        "sensorWidth": "1",
        "sensorHeight": str(colmap_camera.height/colmap_camera.width),
        "serialNumber": "-1",
        "initializationMode": "unknown",
        "initialFocalLength": "-1",
        "pixelRatio": "1",
        "pixelRatioLocked": "true",
        "locked": "true"
        }
        if colmap_camera.model == "SIMPLE_PINHOLE":
            intrinsic["type"]="pinhole"
            intrinsic["focalLength"]=colmap_camera.params[0]
            intrinsic["principalPoint"]=[colmap_camera.params[1], colmap_camera.params[2]]
        if colmap_camera.model == "PINHOLE":
            intrinsic["type"]="pinhole"
            intrinsic["focalLength"]=[colmap_camera.params[0], colmap_camera.params[1]]
            intrinsic["principalPoint"]=[colmap_camera.params[2], colmap_camera.params[3]]
        elif colmap_camera.model == "SIMPLE_RADIAL" :
            intrinsic["type"]="radial1"
            intrinsic["focalLength"]=colmap_camera.params[0]
            intrinsic["principalPoint"]=[colmap_camera.params[1], colmap_camera.params[2]]
            intrinsic["distortionParams"]=[colmap_camera.params[3]]
        else:
            raise RuntimeError("Camera model not supported yet")

        pixel_size = 1/colmap_camera.width
        # converts the focal in "mm", assuming sensor width=1
        if isinstance(intrinsic["focalLength"], list) :
            logger.warning("WARNING: anamorphic lenses not supported, will take mean of intrinsic")
            intrinsic["focalLength"] = np.average(intrinsic["focalLength"])
        intrinsic["focalLength"]=pixel_size*intrinsic["focalLength"]
        # intrinsic["focalLength"]=[pixel_size*x for x in intrinsic["focalLength"]]
        # principal point as delta from center
        intrinsic["principalPoint"]=[intrinsic["principalPoint"][0]-colmap_camera.width/2.0,
                                     intrinsic["principalPoint"][1]-colmap_camera.height/2.0,
                                    ]

        intrinsics.append(intrinsic)
    sfm_data["intrinsics"] = intrinsics
    return sfm_data

# 将colmap的相机外参数据转换为meshroom的相机外参数据
def colmap2meshroom_extrinsics(logger, colmap_extrinsics, colmap_intrinsics, image_folder="", sfm_data={}):
    """
    Convert colmap's extrinsics data to meshroom's extrinsics data
    :param colmap_extrinsics: colmap's extrinsics data
    :param colmap_intrinsics: colmap's intrinsics data
    :param image_folder: image folder path
    :param sfm_data: meshroom's sfm data
    :return: Converted meshroom's sfm data
    """
    sfm_data = sfm_data.copy()
    extrinsics = []
    views = []
    single_cam = False
    if len(colmap_intrinsics) < len(colmap_extrinsics):
        logger.warning("Assuming single camera mode")
        single_cam = True
    for camera_id, colmap_camera in colmap_extrinsics.items():
        try:
            path=colmap_camera.name
            rotation = np.linalg.inv(qvec2rotmat(colmap_camera.qvec))
            translation=rotation@(-colmap_camera.tvec)

            extrinsic = {
                "poseId": camera_id,
                "pose": {
                        "transform": {
                                        "rotation": rotation.flatten().tolist(),
                                        "center": translation.flatten().tolist(),
                                    },
                        "locked": "1"
                        }
            }
            if single_cam:
                intrinsic_id = 1
            else:
                intrinsic_id = camera_id
            view =  {
                    "viewId": camera_id,
                    "poseId": camera_id,
                    "frameId": camera_id,
                    "intrinsicId": intrinsic_id,
                    "path": os.path.join(image_folder, path),
                    "width": colmap_intrinsics[intrinsic_id].width,
                    "height": colmap_intrinsics[intrinsic_id].height
                    }

            views.append(view)
            extrinsics.append(extrinsic)
        except Exception as ex:
            logger.error("Issue with view: "+str(camera_id)+" (skipping) :")
            logger.error(ex)
            continue
    views.sort(key=lambda x: x['viewId'])
    extrinsics.sort(key=lambda x: x['poseId'])
    sfm_data["views"] = views
    sfm_data["poses"] = extrinsics
    return sfm_data


# 将Colmap数据转换为Meshroom格式
def convert_colmap_into_meshroom(logger, colmap_input_path, image_folder_path, sfm_output_path):
    """
    Convert colmap data to meshroom format
    :param colmap_input_path: colmap input path
    :param image_folder_path: image folder path
    :param sfm_output_path: sfm output path
    """
    # 读取colmap的相机内参数据
    colmap_intrinsics = read_cameras_binary(os.path.join(colmap_input_path, "cameras.bin"))
    # 读取colmap的相机外参数据
    colmap_extrinsics = read_images_binary(os.path.join(colmap_input_path, "images.bin"))
    # 初始化meshroom的sfm数据
    sfm_data = {}
    sfm_data["version"] = ["1", "2", "3"]
    # 将colmap的相机内参数据转换为meshroom的相机内参数据
    sfm_data = colmap2meshroom_instrinsics(logger, colmap_intrinsics, sfm_data)
    # 将colmap的相机外参数据转换为meshroom的相机外参数据
    sfm_data = colmap2meshroom_extrinsics(logger, colmap_extrinsics, colmap_intrinsics, image_folder_path, sfm_data)
    # 将meshroom的sfm数据写入到json文件中
    with open(sfm_output_path, "w") as json_file:
        json_file.write(json.dumps(sfm_data, indent=4))
