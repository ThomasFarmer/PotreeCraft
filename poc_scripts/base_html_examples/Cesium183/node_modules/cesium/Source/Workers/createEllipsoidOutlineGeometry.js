/* This file is automatically rebuilt by the Cesium build process. */
define(['./when-f31b6bd1', './EllipsoidOutlineGeometry-54ca925a', './GeometryOffsetAttribute-f6456e72', './Check-ed9ffed2', './Transforms-813bc92c', './Cartesian2-29c15ffd', './Math-03750a0b', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './IndexDatatype-8e4fb082'], function (when, EllipsoidOutlineGeometry, GeometryOffsetAttribute, Check, Transforms, Cartesian2, _Math, RuntimeError, ComponentDatatype, WebGLConstants, GeometryAttribute, GeometryAttributes, IndexDatatype) { 'use strict';

  function createEllipsoidOutlineGeometry(ellipsoidGeometry, offset) {
    if (when.defined(ellipsoidGeometry.buffer)) {
      ellipsoidGeometry = EllipsoidOutlineGeometry.EllipsoidOutlineGeometry.unpack(
        ellipsoidGeometry,
        offset
      );
    }
    return EllipsoidOutlineGeometry.EllipsoidOutlineGeometry.createGeometry(ellipsoidGeometry);
  }

  return createEllipsoidOutlineGeometry;

});
