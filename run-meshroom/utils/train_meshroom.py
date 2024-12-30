import os
import time
import shutil
import random
import string

from .convertColmap2Meshroom import convert_colmap_into_meshroom



def run_camera_init(logger,
                    sensor_database,
                    lens_correction_profile_info,
                    output_path,
                    input_path):
    command = [
        "aliceVision_cameraInit",
        "--sensorDatabase", sensor_database,
        "--lensCorrectionProfileInfo", lens_correction_profile_info,
        "--lensCorrectionProfileSearchIgnoreCameraModel", "True",
        "--defaultFieldOfView", "45.0",
        "--groupCameraFallback", "folder",
        "--allowedCameraModels", "pinhole,radial1,radial3,brown,fisheye4,fisheye1,3deanamorphic4,3deradial4,3declassicld",
        "--rawColorInterpretation", "LibRawWhiteBalancing",
        "--viewIdMethod", "metadata",
        "--verboseLevel", "info",
        "--output", output_path,
        "--allowSingleView", "1",
        "--input", input_path, 
        ">>", os.path.join(os.path.dirname(output_path), "cameraInit.log"),
        "2>&1"
    ]
    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_import_known_poses(logger,
                           sfm_data,
                           known_poses_data,
                           output_path):
    
    command = [
        "aliceVision_importKnownPoses",
        "--sfmData", sfm_data,
        "--knownPosesData", known_poses_data,
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(os.path.dirname(output_path), "importKnownPoses.log"),
        "2>&1"
    ]

    logger.info(" ".join(command))
    os.system(" ".join(command))


def run_feature_extraction(logger,
                           input_path,
                           output_path):
    command = [
        "aliceVision_featureExtraction",
        "--input", input_path,
        "--masksFolder", '""',
        "--maskExtension", "png",
        "--maskInvert", "False",
        "--describerTypes", "dspsift",
        "--describerPreset", "normal",
        "--describerQuality", "normal",
        "--contrastFiltering", "GridSort",
        "--gridFiltering", "True",
        "--workingColorSpace", "sRGB",
        "--forceCpuExtraction", "False",
        "--maxThreads", "0",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(output_path, "featureExtraction.log"),
        "2>&1"
    ]
    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_image_matching(logger,
                       input_path,
                       features_folders,
                       output_path):
    command = [
        "aliceVision_imageMatching",
        "--input", input_path,
        "--featuresFolders", features_folders,
        "--method", "SequentialAndVocabularyTree",
        "--tree", f"{os.environ['ALICEVISION_ROOT']}/share/aliceVision/vlfeat_K80L3.SIFT.tree",
        "--weights", '""',
        "--minNbImages", "200",
        "--maxDescriptors", "500",
        "--nbMatches", "40",
        "--nbNeighbors", "5",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(os.path.dirname(output_path), "imageMatching.log"),
        "2>&1"
    ]
    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_feature_matching(logger,
                         input_path,
                         features_folders,
                         image_pairs_list,
                         output_path):

    command = [
        "aliceVision_featureMatching",
        "--input", input_path,
        "--featuresFolders", features_folders,
        "--imagePairsList", image_pairs_list,
        "--describerTypes", "dspsift",
        "--photometricMatchingMethod", "ANN_L2",
        "--geometricEstimator", "acransac",
        "--geometricFilterType", "fundamental_matrix",
        "--distanceRatio", "0.8",
        "--maxIteration", "2048",
        "--geometricError", "0.0",
        "--knownPosesGeometricErrorMax", "5.0",
        "--minRequired2DMotion", "-1.0",
        "--maxMatches", "0",
        "--savePutativeMatches", "False",
        "--crossMatching", "False",
        "--guidedMatching", "False",
        "--matchFromKnownCameraPoses", "False",
        "--exportDebugFiles", "False",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(output_path, "featureMatching.log"),
        "2>&1"
    ]
    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_structure_from_motion(logger,
                              input_path,
                              features_folders,
                              matches_folders,
                              output_path,
                              output_views_and_poses,
                              extra_info_folder):
    command = [
        "aliceVision_incrementalSfM",
        "--input", input_path,
        "--featuresFolders", features_folders,
        "--matchesFolders", matches_folders,
        "--describerTypes", "dspsift",
        "--localizerEstimator", "acransac",
        "--observationConstraint", "Scale",
        "--localizerEstimatorMaxIterations", "4096",
        "--localizerEstimatorError", "0.0",
        "--lockScenePreviouslyReconstructed", "False",
        "--useLocalBA", "True",
        "--localBAGraphDistance", "1",
        "--nbFirstUnstableCameras", "30",
        "--maxImagesPerGroup", "30",
        "--bundleAdjustmentMaxOutliers", "50",
        "--maxNumberOfMatches", "0",
        "--minNumberOfMatches", "0",
        "--minInputTrackLength", "2",
        "--minNumberOfObservationsForTriangulation", "2",
        "--minAngleForTriangulation", "3.0",
        "--minAngleForLandmark", "2.0",
        "--maxReprojectionError", "4.0",
        "--minAngleInitialPair", "5.0",
        "--maxAngleInitialPair", "40.0",
        "--useOnlyMatchesFromInputFolder", "False",
        "--useRigConstraint", "True",
        "--rigMinNbCamerasForCalibration", "20",
        "--lockAllIntrinsics", "False",
        "--minNbCamerasToRefinePrincipalPoint", "3",
        "--filterTrackForks", "False",
        "--computeStructureColor", "True",
        "--useAutoTransform", "False",
        "--initialPairA", '""',
        "--initialPairB", '""',
        "--interFileExtension", ".abc",
        "--logIntermediateSteps", "False",
        "--verboseLevel", "info",
        "--output", output_path,
        "--outputViewsAndPoses", output_views_and_poses,
        "--extraInfoFolder", extra_info_folder,
        ">>", os.path.join(os.path.dirname(output_path), "structureFromMotion.log"),
        "2>&1"
    ]

    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_prepare_dense_scene(logger,
                            input_path,
                            output_path):
    command = [
        "aliceVision_prepareDenseScene",
        "--input", input_path,
        "--maskExtension", "png",
        "--outputFileType", "exr",
        "--saveMetadata", "True",
        "--saveMatricesTxtFiles", "False",
        "--evCorrection", "False",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(output_path, "prepareDenseScene.log"),
        "2>&1"
    ]
    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_depth_map_estimation(logger,
                             input_path,
                             images_folder,
                             output_path):
    
    command = [
        "aliceVision_depthMapEstimation",
        "--input", input_path,
        "--imagesFolder", images_folder,
        "--downscale", "2",
        "--minViewAngle", "2.0",
        "--maxViewAngle", "70.0",
        "--tileBufferWidth", "1024",
        "--tileBufferHeight", "1024",
        "--tilePadding", "64",
        "--autoAdjustSmallImage", "True",
        "--chooseTCamsPerTile", "True",
        "--maxTCams", "10",
        "--sgmScale", "2",
        "--sgmStepXY", "2",
        "--sgmStepZ", "-1",
        "--sgmMaxTCamsPerTile", "4",
        "--sgmWSH", "4",
        "--sgmUseSfmSeeds", "True",
        "--sgmSeedsRangeInflate", "0.2",
        "--sgmDepthThicknessInflate", "0.0",
        "--sgmMaxSimilarity", "1.0",
        "--sgmGammaC", "5.5",
        "--sgmGammaP", "8.0",
        "--sgmP1", "10.0",
        "--sgmP2Weighting", "100.0",
        "--sgmMaxDepths", "1500",
        "--sgmFilteringAxes", "YX",
        "--sgmDepthListPerTile", "True",
        "--sgmUseConsistentScale", "False",
        "--refineEnabled", "True",
        "--refineScale", "1",
        "--refineStepXY", "1",
        "--refineMaxTCamsPerTile", "4",
        "--refineSubsampling", "10",
        "--refineHalfNbDepths", "15",
        "--refineWSH", "3",
        "--refineSigma", "15.0",
        "--refineGammaC", "15.5",
        "--refineGammaP", "8.0",
        "--refineInterpolateMiddleDepth", "False",
        "--refineUseConsistentScale", "False",
        "--colorOptimizationEnabled", "True",
        "--colorOptimizationNbIterations", "100",
        "--sgmUseCustomPatchPattern", "False",
        "--refineUseCustomPatchPattern", "False",
        "--exportIntermediateDepthSimMaps", "False",
        "--exportIntermediateNormalMaps", "False",
        "--exportIntermediateVolumes", "False",
        "--exportIntermediateCrossVolumes", "False",
        "--exportIntermediateTopographicCutVolumes", "False",
        "--exportIntermediateVolume9pCsv", "False",
        "--exportTilePattern", "False",
        "--nbGPUs", "0",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(output_path, "depthMapEstimation.log"),
        "2>&1"
    ]

    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_depth_map_filtering(logger,
                            input_path,
                            depth_maps_folder,
                            output_path):
    
    command = [
        "aliceVision_depthMapFiltering",
        "--input", input_path,
        "--depthMapsFolder", depth_maps_folder,
        "--minViewAngle", "2.0",
        "--maxViewAngle", "70.0",
        "--nNearestCams", "10",
        "--minNumOfConsistentCams", "3",
        "--minNumOfConsistentCamsWithLowSimilarity", "4",
        "--pixToleranceFactor", "2.0",
        "--pixSizeBall", "0",
        "--pixSizeBallWithLowSimilarity", "0",
        "--computeNormalMaps", "False",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(output_path, "depthMapFiltering.log"),
        "2>&1"
    ]
    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_meshing(logger,
                input_path,
                depth_maps_folder,
                output_mesh,
                output_path):
    
    command = [
        "aliceVision_meshing",
        "--input", input_path,
        "--depthMapsFolder", depth_maps_folder,
        "--estimateSpaceFromSfM", "True",
        "--estimateSpaceMinObservations", "3",
        "--estimateSpaceMinObservationAngle", "10.0",
        "--maxInputPoints", "50000000",
        "--maxPoints", "5000000",
        "--maxPointsPerVoxel", "1000000",
        "--minStep", "2",
        "--partitioning", "singleBlock",
        "--repartition", "multiResolution",
        "--angleFactor", "15.0",
        "--simFactor", "15.0",
        "--minVis", "2",
        "--pixSizeMarginInitCoef", "2.0",
        "--pixSizeMarginFinalCoef", "4.0",
        "--voteMarginFactor", "4.0",
        "--contributeMarginFactor", "2.0",
        "--simGaussianSizeInit", "10.0",
        "--simGaussianSize", "10.0",
        "--minAngleThreshold", "1.0",
        "--refineFuse", "True",
        "--helperPointsGridSize", "10",
        "--nPixelSizeBehind", "4.0",
        "--fullWeight", "1.0",
        "--voteFilteringForWeaklySupportedSurfaces", "True",
        "--addLandmarksToTheDensePointCloud", "False",
        "--invertTetrahedronBasedOnNeighborsNbIterations", "10",
        "--minSolidAngleRatio", "0.2",
        "--nbSolidAngleFilteringIterations", "2",
        "--colorizeOutput", "False",
        "--maxNbConnectedHelperPoints", "50",
        "--saveRawDensePointCloud", "False",
        "--exportDebugTetrahedralization", "False",
        "--seed", "0",
        "--verboseLevel", "info",
        "--outputMesh", output_mesh,
        "--output", output_path,
        ">>", os.path.join(os.path.dirname(output_path), "meshing.log"),
        "2>&1"
    ]

    logger.info(" ".join(command))
    os.system(" ".join(command))


def run_mesh_filtering(logger,
                       input_mesh,
                       output_mesh):
    
    command = [
        "aliceVision_meshFiltering",
        "--inputMesh", input_mesh,
        "--keepLargestMeshOnly", "False",
        "--smoothingSubset", "all",
        "--smoothingBoundariesNeighbours", "0",
        "--smoothingIterations", "5",
        "--smoothingLambda", "1.0",
        "--filteringSubset", "all",
        "--filteringIterations", "1",
        "--filterLargeTrianglesFactor", "60.0",
        "--filterTrianglesRatio", "0.0",
        "--verboseLevel", "info",
        "--outputMesh", output_mesh,
        ">>", os.path.join(os.path.dirname(output_mesh), "meshFiltering.log"),
        "2>&1"
    ]

    logger.info(" ".join(command))
    os.system(" ".join(command))

def run_texturing(logger,
                  input_path,
                  images_folder,
                  input_mesh,
                  output_path):
    
    command = [
        "aliceVision_texturing",
        "--input", input_path,
        "--imagesFolder", images_folder,
        "--inputMesh", input_mesh,
        "--inputRefMesh", '""',
        "--textureSide", "8192",
        "--downscale", "2",
        "--outputMeshFileType", "obj",
        "--colorMappingFileType", "png",
        "--unwrapMethod", "Basic",
        "--useUDIM", "True",
        "--fillHoles", "False",
        "--padding", "5",
        "--multiBandDownscale", "4",
        "--multiBandNbContrib", "1", "5", "10", "0",
        "--useScore", "True",
        "--bestScoreThreshold", "0.1",
        "--angleHardThreshold", "90.0",
        "--workingColorSpace", "sRGB",
        "--outputColorSpace", "AUTO",
        "--correctEV", "True",
        "--forceVisibleByAllVertices", "False",
        "--flipNormals", "False",
        "--visibilityRemappingMethod", "PullPush",
        "--subdivisionTargetRatio", "0.8",
        "--verboseLevel", "info",
        "--output", output_path,
        ">>", os.path.join(output_path, "texturing.log"),
        "2>&1"
    ]

    logger.info(" ".join(command))
    os.system(" ".join(command))


def recalibrate_mesh_coordinates(logger,
                                 input_mesh_path, 
                                 output_mesh_path):
    """
    逆转mesh坐标系。

    这个函数读取输入的mesh文件，逆转其坐标系（x, y, z -> x, -y, -z），然后将结果写入到输出文件中。

    参数:
    - input_mesh_path (str): 输入mesh文件的路径。
    - output_mesh_path (str): 输出mesh文件的路径。
    """
    if not input_mesh_path.endswith('.obj'):
        logger.error(f"输入的mesh路径 {input_mesh_path} 不是以 .obj 结尾的文件。")
        raise ValueError(f"输入的mesh路径 {input_mesh_path} 不是以 .obj 结尾的文件。")
    if not output_mesh_path.endswith('.obj'):
        logger.error(f"输出的mesh路径 {output_mesh_path} 不是以 .obj 结尾的文件。")
        raise ValueError(f"输出的mesh路径 {output_mesh_path} 不是以 .obj 结尾的文件。")
    
    with open(input_mesh_path, 'r') as f:
        lines = f.readlines()

    reversed_lines = []

    for line in lines:
        if line.startswith('v '):
            coords = line.split()[1:]
            x, y, z = map(float, coords)
            new_x, new_y, new_z = x, -y, -z
            new_line = f'v {new_x} {new_y} {new_z}\n'
            reversed_lines.append(new_line)
        else:
            reversed_lines.append(line)

    with open(output_mesh_path, 'w') as f:
        f.writelines(reversed_lines)
    
    logger.info(f"Mesh坐标系逆转完成，输出路径: {output_mesh_path}")

def run_publish(logger,
                input_path,
                output_path):
    """
    发布Meshroom处理后的结果。

    这个函数将Meshroom处理后的结果从输入路径复制到输出路径，并对obj文件进行坐标系逆转处理。

    参数:
    - input_path (str): 输入路径，包含Meshroom处理后的结果。
    - output_path (str): 输出路径，将Meshroom处理后的结果复制到这里。
    """

    # 定义要复制的文件扩展名
    extensions = [".obj", ".mtl", ".png"]

    # 复制文件到输出文件夹
    for ext in extensions:
        for file in os.listdir(input_path):
            if file.endswith(ext):
                shutil.copy(os.path.join(input_path, file), output_path)
            if file.endswith(".obj"):
                recalibrate_mesh_coordinates(
                    logger=logger,
                    input_mesh_path=os.path.join(input_path, file),
                    output_mesh_path=os.path.join(output_path, file)
                )
    
    logger.info(f"Meshroom处理后的结果发布完成，输出路径: {output_path}")
    return


def set_env_variables(alicevision_install):
    os.environ["ALICEVISION_ROOT"] = alicevision_install
    os.environ["ALICEVISION_INSTALL"] = alicevision_install
    os.environ["ALICEVISION_SENSOR_DB"] = f"{alicevision_install}/share/aliceVision/cameraSensors.db"
    os.environ["LD_LIBRARY_PATH"] = f"{alicevision_install}/lib:/usr/lib/nvidia-384:/usr/local/cuda-8.0/lib64/:{os.environ.get('LD_LIBRARY_PATH', '')}"
    os.environ["PATH"] += os.pathsep + f"{alicevision_install}/bin"


def random_string(length):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def run_meshroom_pipeline(colmap_input_path, image_folder_path, meshroom_cache_path, meshroom_output_path, logger):
    """
    运行Meshroom管道。

    这个函数运行Meshroom管道，将Colmap数据转换为Meshroom格式，并进行一系列处理，最终生成纹理贴图。

    参数:
    - colmap_input_path (str): Colmap输入路径，包含稀疏重建数据。
        case_folder/sparse/0
    - image_folder_path (str): 图像文件夹路径，包含所有图像。
        case_folder/images
    """
    pipeline_start_time = time.time()
    logger.info("开始运行Meshroom管道...")
    
    # 创建Meshroom缓存目录
    os.makedirs(meshroom_cache_path, exist_ok=True)
    logger.info(f"Meshroom缓存目录已创建: {meshroom_cache_path}")

    colmap_sfm_output_path = os.path.join(meshroom_cache_path, "colmap_sfm", "cameras.sfm")
    logger.info(f"将Colmap数据转换为Meshroom格式，输出路径: {colmap_sfm_output_path}")
    os.makedirs(os.path.dirname(colmap_sfm_output_path), exist_ok=True)
    start = time.time()
    convert_colmap_into_meshroom(
        logger=logger,
        colmap_input_path=colmap_input_path, 
        image_folder_path=image_folder_path, 
        sfm_output_path=colmap_sfm_output_path
    )
    end = time.time()
    logger.info(f"Colmap数据转换完成，用时: {end - start} 秒")

    # 运行 CameraInit
    
    camera_init_random_code = random_string(8)
    camera_init_output_path = os.path.join(meshroom_cache_path, f"CameraInit/{camera_init_random_code}/cameraInit.sfm")
    camera_init_input_path = os.path.join(meshroom_cache_path, f"CameraInit/{camera_init_random_code}/viewpoints.sfm")
    os.makedirs(os.path.dirname(camera_init_output_path), exist_ok=True)  # 创建路径
    logger.info(f"运行CameraInit，输出路径: {camera_init_output_path}")
    start = time.time() 
    run_camera_init(
        logger=logger,
        sensor_database="${ALICEVISION_SENSOR_DB}", 
        lens_correction_profile_info="${ALICEVISION_LENS_PROFILE_INFO}", 
        output_path=camera_init_output_path,
        input_path=camera_init_input_path
    )
    end = time.time()
    logger.info(f"CameraInit完成，用时: {end - start} 秒")

    # 运行 ImportKnownPoses (如果有已知位姿数据的话)
    import_known_poses_random_code = random_string(8)
    import_known_poses_output_path = os.path.join(meshroom_cache_path, f"ImportKnownPoses/{import_known_poses_random_code}/sfmData.abc")
    os.makedirs(os.path.dirname(import_known_poses_output_path), exist_ok=True)  # 创建路径
    logger.info(f"运行ImportKnownPoses，输出路径: {import_known_poses_output_path}")
    start = time.time()
    run_import_known_poses(
        logger=logger,
        sfm_data=colmap_sfm_output_path,
        known_poses_data='""',
        output_path=import_known_poses_output_path,
    )
    end = time.time()
    logger.info(f"ImportKnownPoses完成，用时: {end - start} 秒")

    # 运行 FeatureExtraction
    feature_extraction_random_code = random_string(8)
    feature_extraction_output_path = os.path.join(meshroom_cache_path, f"FeatureExtraction/{feature_extraction_random_code}")
    os.makedirs(feature_extraction_output_path, exist_ok=True)  # 创建路径
    logger.info(f"运行FeatureExtraction，输出路径: {feature_extraction_output_path}")
    start = time.time()
    run_feature_extraction(
        logger=logger,
        input_path=import_known_poses_output_path,
        output_path=feature_extraction_output_path
    )
    end = time.time()
    logger.info(f"FeatureExtraction完成，用时: {end - start} 秒")

    # 运行 ImageMatching
    image_matching_random_code = random_string(8)
    image_matching_output_path = os.path.join(meshroom_cache_path, f"ImageMatching/{image_matching_random_code}/imageMatches.txt")
    os.makedirs(os.path.dirname(image_matching_output_path), exist_ok=True)  # 创建路径
    logger.info(f"运行ImageMatching，输出路径: {image_matching_output_path}")
    start = time.time()
    run_image_matching(
        logger=logger,
        input_path=import_known_poses_output_path,
        features_folders=feature_extraction_output_path,
        output_path=image_matching_output_path
    )
    end = time.time()
    logger.info(f"ImageMatching完成，用时: {end - start} 秒")

    # 运行 FeatureMatching
    feature_matching_random_code = random_string(8)
    feature_matching_output_path = os.path.join(meshroom_cache_path, f"FeatureMatching/{feature_matching_random_code}")
    os.makedirs(feature_matching_output_path, exist_ok=True)  # 创建路径
    logger.info(f"运行FeatureMatching，输出路径: {feature_matching_output_path}")
    start = time.time()
    run_feature_matching(
        logger=logger,
        input_path=import_known_poses_output_path,
        features_folders=feature_extraction_output_path,
        image_pairs_list=image_matching_output_path,
        output_path=feature_matching_output_path
    )
    end = time.time()
    logger.info(f"FeatureMatching完成，用时: {end - start} 秒")

    # 运行 StructureFromMotion
    structure_from_motion_random_code = random_string(8)
    sfm_output_path = os.path.join(meshroom_cache_path, f"StructureFromMotion/{structure_from_motion_random_code}/sfm.abc")
    cameras_output_path = os.path.join(meshroom_cache_path, f"StructureFromMotion/{structure_from_motion_random_code}/cameras.sfm")
    extra_info_folder = os.path.join(meshroom_cache_path, f"StructureFromMotion/{structure_from_motion_random_code}")
    os.makedirs(extra_info_folder, exist_ok=True)  # 创建路径
    logger.info(f"运行StructureFromMotion，输出路径: {sfm_output_path}")
    start = time.time()
    run_structure_from_motion(
        logger=logger,
        input_path=import_known_poses_output_path, 
        features_folders=feature_extraction_output_path,
        matches_folders=feature_matching_output_path,
        output_path=sfm_output_path,
        output_views_and_poses=cameras_output_path,
        extra_info_folder=extra_info_folder
    )
    end = time.time()
    logger.info(f"StructureFromMotion完成，用时: {end - start} 秒")

    # 运行 PrepareDenseScene
    prepare_dense_scene_random_code = random_string(8)
    prepare_dense_scene_output_path = os.path.join(meshroom_cache_path, f"PrepareDenseScene/{prepare_dense_scene_random_code}")
    os.makedirs(prepare_dense_scene_output_path, exist_ok=True)  # 创建路径
    logger.info(f"运行PrepareDenseScene，输出路径: {prepare_dense_scene_output_path}")
    start = time.time()
    run_prepare_dense_scene(
        logger=logger,
        input_path=sfm_output_path,
        output_path=prepare_dense_scene_output_path
    )
    end = time.time()
    logger.info(f"PrepareDenseScene完成，用时: {end - start} 秒")

    # 运行 DepthMapEstimation
    depth_map_estimation_random_code = random_string(8)
    depth_map_estimation_output_path = os.path.join(meshroom_cache_path, f"DepthMap/{depth_map_estimation_random_code}")
    os.makedirs(depth_map_estimation_output_path, exist_ok=True)  # 创建路径
    logger.info(f"运行DepthMapEstimation，输出路径: {depth_map_estimation_output_path}")
    start = time.time()
    run_depth_map_estimation(
        logger=logger,
        input_path=sfm_output_path,
        images_folder=prepare_dense_scene_output_path,
        output_path=depth_map_estimation_output_path
    )
    end = time.time()
    logger.info(f"DepthMapEstimation完成，用时: {end - start} 秒")

    # 运行 DepthMapFiltering
    depth_map_filtering_random_code = random_string(8)
    depth_map_filtering_output_path = os.path.join(meshroom_cache_path, f"DepthMapFilter/{depth_map_filtering_random_code}")
    os.makedirs(depth_map_filtering_output_path, exist_ok=True)  # 创建路径
    logger.info(f"运行DepthMapFiltering，输出路径: {depth_map_filtering_output_path}")
    start = time.time()
    run_depth_map_filtering(
        logger=logger,
        input_path=sfm_output_path,
        depth_maps_folder=depth_map_estimation_output_path,
        output_path=depth_map_filtering_output_path
    )
    end = time.time()
    logger.info(f"DepthMapFiltering完成，用时: {end - start} 秒")

    # 运行 Meshing
    meshing_random_code = random_string(8)
    meshing_output_mesh = os.path.join(meshroom_cache_path, f"Meshing/{meshing_random_code}/mesh.obj")
    meshing_output_path = os.path.join(meshroom_cache_path, f"Meshing/{meshing_random_code}/densePointCloud.abc")
    os.makedirs(os.path.dirname(meshing_output_mesh), exist_ok=True)  # 创建路径
    logger.info(f"运行Meshing，输出路径: {meshing_output_path}")
    start = time.time()
    run_meshing(
        logger=logger,
        input_path=sfm_output_path,
        depth_maps_folder=depth_map_filtering_output_path,
        output_mesh=meshing_output_mesh,
        output_path=meshing_output_path
    )
    end = time.time()
    logger.info(f"Meshing完成，用时: {end - start} 秒")

    # 运行 MeshFiltering
    mesh_filtering_random_code = random_string(8)
    mesh_filtering_input_mesh = meshing_output_mesh
    mesh_filtering_output_mesh = os.path.join(meshroom_cache_path, f"MeshFiltering/{mesh_filtering_random_code}/mesh.obj")
    os.makedirs(os.path.dirname(mesh_filtering_output_mesh), exist_ok=True)  # 创建路径
    logger.info(f"运行MeshFiltering，输出路径: {mesh_filtering_output_mesh}")
    start = time.time()
    run_mesh_filtering(
        logger=logger,
        input_mesh=mesh_filtering_input_mesh,
        output_mesh=mesh_filtering_output_mesh
    )
    end = time.time()
    logger.info(f"MeshFiltering完成，用时: {end - start} 秒")

    # 运行 Texturing
    texturing_random_code = random_string(8)
    texturing_output_path = os.path.join(meshroom_cache_path, f"Texturing/{texturing_random_code}")
    os.makedirs(texturing_output_path, exist_ok=True)  # 创建路径
    logger.info(f"运行Texturing，输出路径: {texturing_output_path}")
    start = time.time()
    run_texturing(
        logger=logger,
        input_path=meshing_output_path,
        images_folder=prepare_dense_scene_output_path,
        input_mesh=mesh_filtering_output_mesh,
        output_path=texturing_output_path
    )
    end = time.time()
    logger.info(f"Texturing完成，用时: {end - start} 秒")

    # 运行 Publish
    logger.info(f"运行Publish，输出路径: {meshroom_output_path}")
    start = time.time()
    os.makedirs(meshroom_output_path, exist_ok=True)  # 创建路径
    run_publish(
        logger=logger,
        input_path=texturing_output_path,
        output_path=meshroom_output_path
    )
    end = time.time()
    logger.info(f"Publish完成，用时: {end - start} 秒")

    pipeline_end_time = time.time()
    logger.info(f"Meshroom管道运行完成，总用时: {pipeline_end_time - pipeline_start_time} 秒")

