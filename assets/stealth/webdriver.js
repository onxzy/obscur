// ==UserScript==
// @name         Webdriver
// @namespace    http://tampermonkey.net/
// @version      2024-11-20
// @description  try to take over the world!
// @author       You
// @match        *://*/*
// @grant        none
// @run-at        document-start
// ==/UserScript==

(function() {
  'use strict';
  delete Object.getPrototypeOf(navigator).webdriver;
})();