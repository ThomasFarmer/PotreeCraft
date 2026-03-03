/* This file is automatically rebuilt by the Cesium build process. */
define(['./when-f31b6bd1', './FrustumGeometry-943a044b', './Transforms-813bc92c', './Cartesian2-29c15ffd', './Check-ed9ffed2', './Math-03750a0b', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './Plane-55754a2b', './VertexFormat-44d61ac9'], function (when, FrustumGeometry, Transforms, Cartesian2, Check, _Math, RuntimeError, ComponentDatatype, WebGLConstants, GeometryAttribute, GeometryAttributes, Plane, VertexFormat) { 'use strict';

  function createFrustumGeometry(frustumGeometry, offset) {
    if (when.defined(offset)) {
      frustumGeometry = FrustumGeometry.FrustumGeometry.unpack(frustumGeometry, offset);
    }
    return FrustumGeometry.FrustumGeometry.createGeometry(frustumGeometry);
  }

  return createFrustumGeometry;

});
