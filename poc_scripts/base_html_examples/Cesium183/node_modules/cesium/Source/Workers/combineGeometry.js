/* This file is automatically rebuilt by the Cesium build process. */
define(['./PrimitivePipeline-a595a3ab', './createTaskProcessorWorker', './Transforms-813bc92c', './Cartesian2-29c15ffd', './Check-ed9ffed2', './when-f31b6bd1', './Math-03750a0b', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './GeometryPipeline-0f2492f2', './AttributeCompression-69f7b4c3', './EncodedCartesian3-3efd178b', './IndexDatatype-8e4fb082', './IntersectionTests-c1eea555', './Plane-55754a2b', './WebMercatorProjection-98814ec7'], function (PrimitivePipeline, createTaskProcessorWorker, Transforms, Cartesian2, Check, when, _Math, RuntimeError, ComponentDatatype, WebGLConstants, GeometryAttribute, GeometryAttributes, GeometryPipeline, AttributeCompression, EncodedCartesian3, IndexDatatype, IntersectionTests, Plane, WebMercatorProjection) { 'use strict';

  function combineGeometry(packedParameters, transferableObjects) {
    var parameters = PrimitivePipeline.PrimitivePipeline.unpackCombineGeometryParameters(
      packedParameters
    );
    var results = PrimitivePipeline.PrimitivePipeline.combineGeometry(parameters);
    return PrimitivePipeline.PrimitivePipeline.packCombineGeometryResults(
      results,
      transferableObjects
    );
  }
  var combineGeometry$1 = createTaskProcessorWorker(combineGeometry);

  return combineGeometry$1;

});
