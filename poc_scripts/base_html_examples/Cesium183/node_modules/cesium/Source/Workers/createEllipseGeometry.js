/* This file is automatically rebuilt by the Cesium build process. */
define(['./Cartesian2-29c15ffd', './when-f31b6bd1', './EllipseGeometry-743b2a41', './Check-ed9ffed2', './Math-03750a0b', './GeometryOffsetAttribute-f6456e72', './Transforms-813bc92c', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './EllipseGeometryLibrary-e9a0b750', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './GeometryInstance-872cd25f', './GeometryPipeline-0f2492f2', './AttributeCompression-69f7b4c3', './EncodedCartesian3-3efd178b', './IndexDatatype-8e4fb082', './IntersectionTests-c1eea555', './Plane-55754a2b', './VertexFormat-44d61ac9'], function (Cartesian2, when, EllipseGeometry, Check, _Math, GeometryOffsetAttribute, Transforms, RuntimeError, ComponentDatatype, WebGLConstants, EllipseGeometryLibrary, GeometryAttribute, GeometryAttributes, GeometryInstance, GeometryPipeline, AttributeCompression, EncodedCartesian3, IndexDatatype, IntersectionTests, Plane, VertexFormat) { 'use strict';

  function createEllipseGeometry(ellipseGeometry, offset) {
    if (when.defined(offset)) {
      ellipseGeometry = EllipseGeometry.EllipseGeometry.unpack(ellipseGeometry, offset);
    }
    ellipseGeometry._center = Cartesian2.Cartesian3.clone(ellipseGeometry._center);
    ellipseGeometry._ellipsoid = Cartesian2.Ellipsoid.clone(ellipseGeometry._ellipsoid);
    return EllipseGeometry.EllipseGeometry.createGeometry(ellipseGeometry);
  }

  return createEllipseGeometry;

});
