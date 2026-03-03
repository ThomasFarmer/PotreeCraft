/* This file is automatically rebuilt by the Cesium build process. */
define(['./when-f31b6bd1', './PrimitivePipeline-a595a3ab', './createTaskProcessorWorker', './Transforms-813bc92c', './Cartesian2-29c15ffd', './Check-ed9ffed2', './Math-03750a0b', './RuntimeError-c7c236f3', './ComponentDatatype-6fe28ef7', './WebGLConstants-0664004c', './GeometryAttribute-f3100ea3', './GeometryAttributes-e973821e', './GeometryPipeline-0f2492f2', './AttributeCompression-69f7b4c3', './EncodedCartesian3-3efd178b', './IndexDatatype-8e4fb082', './IntersectionTests-c1eea555', './Plane-55754a2b', './WebMercatorProjection-98814ec7'], function (when, PrimitivePipeline, createTaskProcessorWorker, Transforms, Cartesian2, Check, _Math, RuntimeError, ComponentDatatype, WebGLConstants, GeometryAttribute, GeometryAttributes, GeometryPipeline, AttributeCompression, EncodedCartesian3, IndexDatatype, IntersectionTests, Plane, WebMercatorProjection) { 'use strict';

  /* global require */

  var moduleCache = {};

  function getModule(moduleName) {
    var module = moduleCache[moduleName];
    if (!when.defined(module)) {
      if (typeof exports === "object") {
        // Use CommonJS-style require.
        moduleCache[module] = module = require("Workers/" + moduleName);
      } else {
        // Use AMD-style require.
        // in web workers, require is synchronous
        require(["Workers/" + moduleName], function (f) {
          module = f;
          moduleCache[module] = f;
        });
      }
    }
    return module;
  }

  function createGeometry(parameters, transferableObjects) {
    var subTasks = parameters.subTasks;
    var length = subTasks.length;
    var resultsOrPromises = new Array(length);

    for (var i = 0; i < length; i++) {
      var task = subTasks[i];
      var geometry = task.geometry;
      var moduleName = task.moduleName;

      if (when.defined(moduleName)) {
        var createFunction = getModule(moduleName);
        resultsOrPromises[i] = createFunction(geometry, task.offset);
      } else {
        //Already created geometry
        resultsOrPromises[i] = geometry;
      }
    }

    return when.when.all(resultsOrPromises, function (results) {
      return PrimitivePipeline.PrimitivePipeline.packCreateGeometryResults(
        results,
        transferableObjects
      );
    });
  }
  var createGeometry$1 = createTaskProcessorWorker(createGeometry);

  return createGeometry$1;

});
