/* This file is automatically rebuilt by the Cesium build process. */
define(['./CylinderGeometry-a090aac2', './when-f31b6bd1', './GeometryOffsetAttribute-f6456e72', './Check-ed9ffed2', './Transforms-813bc92c', './Cartesian2-29c15ffd', './Math-03750a0b', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './CylinderGeometryLibrary-a5923d2f', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './IndexDatatype-8e4fb082', './VertexFormat-44d61ac9'], function (CylinderGeometry, when, GeometryOffsetAttribute, Check, Transforms, Cartesian2, _Math, RuntimeError, ComponentDatatype, WebGLConstants, CylinderGeometryLibrary, GeometryAttribute, GeometryAttributes, IndexDatatype, VertexFormat) { 'use strict';

  function createCylinderGeometry(cylinderGeometry, offset) {
    if (when.defined(offset)) {
      cylinderGeometry = CylinderGeometry.CylinderGeometry.unpack(cylinderGeometry, offset);
    }
    return CylinderGeometry.CylinderGeometry.createGeometry(cylinderGeometry);
  }

  return createCylinderGeometry;

});
