# Changelog

## [1.4.0](https://github.com/PeterMosmans/apdfhelper/compare/1.3.0...1.4.0) (2025-07-14)


### Features

* add main function ([6549a5d](https://github.com/PeterMosmans/apdfhelper/commit/6549a5d058af36a9e39c3c59b794a0642f1b03df))
* add project file ([b5ca3b1](https://github.com/PeterMosmans/apdfhelper/commit/b5ca3b1ac2af4ddb31313f405d00fc138f0fa477))
* improve project file ([8523cf2](https://github.com/PeterMosmans/apdfhelper/commit/8523cf2b4153c4e8683c0b78921a141b548f738a))
* update project file ([3cf4d07](https://github.com/PeterMosmans/apdfhelper/commit/3cf4d072c005ff3cd887f3ef6777fe9a0f827729))

## [1.3.0](https://github.com/PeterMosmans/apdfhelper/compare/1.2.0...1.3.0) (2024-01-04)


### Features

* add cut and swap functions ([535a73f](https://github.com/PeterMosmans/apdfhelper/commit/535a73fa530eb1f632f8cabea09099f37de5d6e3))
* add option to duplicate a page ([e86f360](https://github.com/PeterMosmans/apdfhelper/commit/e86f360ceb294a37da04e0690225d14ff191f213))
* add option to inject page from another file ([cb38628](https://github.com/PeterMosmans/apdfhelper/commit/cb386281b620a9bbc63174eecade5ac76c841312))
* allow named links to point to toc titles ([3285c01](https://github.com/PeterMosmans/apdfhelper/commit/3285c01b2d3474703087b949c1a1155270c07273))
* improve error handling for undefined toc entries ([3139ffa](https://github.com/PeterMosmans/apdfhelper/commit/3139ffae6694670dfa8c50fa64a4d19b480609b5))
* support nested table of contents ([05f145f](https://github.com/PeterMosmans/apdfhelper/commit/05f145fce5e0676d9deb53e97b38cb81102156c2))


### Bug Fixes

* catch specific exceptions ([9b19d2b](https://github.com/PeterMosmans/apdfhelper/commit/9b19d2b9e0eba2127ba43c471d03aff594de2fad))
* deal with multiple data structures ([4fdb55f](https://github.com/PeterMosmans/apdfhelper/commit/4fdb55f57f94d423002675ddf568c98b2ad5473a))
* use correct function names for toc titles ([98950a6](https://github.com/PeterMosmans/apdfhelper/commit/98950a646956265c7ba905fe85c25547f7d4162f))
* use correct naming for variable ([485ec98](https://github.com/PeterMosmans/apdfhelper/commit/485ec985ce24f05e8f97714cc972942590e3b844))

## [1.2.0](https://github.com/PeterMosmans/apdfhelper/compare/1.1.0...1.2.0) (2023-11-07)


### Features

* add --verbose option to most commands ([f2054de](https://github.com/PeterMosmans/apdfhelper/commit/f2054de06a2193f95c1928be02119d25731fa370))
* add option to save PDF using faster algorithm ([d4f6942](https://github.com/PeterMosmans/apdfhelper/commit/d4f69424fd3ea7626734fa58a6f6590910f95049))
* convert page numbers to bookmark titles for notes ([ca9a627](https://github.com/PeterMosmans/apdfhelper/commit/ca9a6277b3b89da96f2f4dc9a12b6ead9e47ad03))
* support nested bookmarks ([bda75f9](https://github.com/PeterMosmans/apdfhelper/commit/bda75f9f45fd6e2497248f7e8710c0a7ac6d21c2))
* table of contents can be used to rewrite named links ([94411a5](https://github.com/PeterMosmans/apdfhelper/commit/94411a5b1f91c00b1fd625f1063d2a65733faa58))
* use last toc title for page title instead of first one ([c194235](https://github.com/PeterMosmans/apdfhelper/commit/c19423516a50c0f736d624737111a15793f95882))
* use toc and tocfile for consistency ([f5a1c79](https://github.com/PeterMosmans/apdfhelper/commit/f5a1c79d16c4b8c70105298d7501919630582a19))


### Bug Fixes

* ensure that bookmarks are displayed in the correct input format ([7e06e26](https://github.com/PeterMosmans/apdfhelper/commit/7e06e26313c34430411fd51292f642521e189a6a))
* show correct number of bookmarked items ([464173f](https://github.com/PeterMosmans/apdfhelper/commit/464173f8df8bcebdbb8e737a8037ce8bc4914060))

## [1.1.0](https://github.com/PeterMosmans/apdfhelper/compare/1.0.0...1.1.0) (2023-11-06)


### Features

* add function to split PDF file ([5f20b82](https://github.com/PeterMosmans/apdfhelper/commit/5f20b82fd3597d08fadb524d385b9d3a1f189882))
* add option to show details for notes ([124ab3c](https://github.com/PeterMosmans/apdfhelper/commit/124ab3c289381a2014f5397da5531160cc91ade2))
* support reading and adding bookmarks ([9cc3f9e](https://github.com/PeterMosmans/apdfhelper/commit/9cc3f9ea8143d4a24e88a6a26de0fd28c3e04bb9))
* support the use of dictionary files ([4f53757](https://github.com/PeterMosmans/apdfhelper/commit/4f53757763a375455da4683a5fe08d979740cc25))


### Bug Fixes

* handle errors in dictionary file better ([d5aba57](https://github.com/PeterMosmans/apdfhelper/commit/d5aba57a870b79f15cbead0896cff3ca467831c1))

## 1.0.0 (2023-11-02)


### Features

* initial version ([8fa374f](https://github.com/PeterMosmans/apdfhelper/commit/8fa374fc46f6ea0cce39143f55ff003aa00f3d96))
* specify ranges for deletion ([48191d8](https://github.com/PeterMosmans/apdfhelper/commit/48191d890c054f36d886ea416fc8263de2a33326))
