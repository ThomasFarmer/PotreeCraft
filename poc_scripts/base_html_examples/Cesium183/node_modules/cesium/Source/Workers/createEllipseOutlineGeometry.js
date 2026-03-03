/* This file is automatically rebuilt by the Cesium build process. */
define(['./Cartesian2-29c15ffd', './when-f31b6bd1', './EllipseOutlineGeometry-d2de4c36', './Check-ed9ffed2', './Math-03750a0b', './GeometryOffsetAttribute-f6456e72', './Transforms-813bc92c', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './EllipseGeometryLibrary-e9a0b750', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './IndexDatatype-8e4fb082'], function (Cartesian2, when, EllipseOutlineGeometry, Check, _Math, GeometryOffsetAttribute, Transforms, RuntimeError, ComponentDatatype, WebGLConstants, EllipseGeometryLibrary, GeometryAttribute, GeometryAttributes, IndexDatatype) { 'use strict';

  function createEllipseOutlineGeometry(ellipseGeometry, offset) {
    if (when.defined(offset)) {
      ellipseGeometry = EllipseOutlineGeometry.EllipseOutlineGeometry.unpack(ellipseGeometry, offset);
    }
    ellipseGeometry._center = Cartesian2.Cartesian3.clone(ellipseGeometry._center);
    ellipseGeometry._ellipsoid = Cartesian2.Ellipsoid.clone(ellipseGeometry._ellipsoid);
    return EllipseOutlineGeometry.EllipseOutlineGeometry.createGeometry(ellipseGeometry);
  }

  return createEllipseOutlineGeometry;

});
