# Third-party notices

## QueryForge and COFORGE-derived design material

DwellProof's color tokens and blue-to-green gradient are derived through
COFORGE at commit
`98dacb70ddd0c550daa7059e5fdf364a7ff579d4`. The shared color-token block also
appears in QueryForge at commit
`ce663ac8d7ab432d0923c2f077bae02ae2b34a8e`. The source projects are available
at `https://github.com/eric-stone-plus/COFORGE` and
`https://github.com/eric-stone-plus/QueryForge`. The gradient is also used
within DwellProof-specific favicon and application icons.

The color-token block in `web/app/globals.css` has been extended and modified
for DwellProof's evidence workbench, responsive layout, and print presentation.

The QueryForge-derived portion retains this notice:

Copyright 2026 QueryForge contributors

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this material except in compliance with the License. You may obtain a copy of
the License at `https://www.apache.org/licenses/LICENSE-2.0`. Unless required by
applicable law or agreed to in writing, software distributed under the License
is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the specific language
governing permissions and limitations under the License. The complete license
text is retained in `licenses/QueryForge-APACHE-2.0.txt`.

The COFORGE-derived portion retains the following notice and license:

MIT License

Copyright (c) 2026 COFORGE contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## T3 Code visual language

The 2026-07-19 workbench redesign references the visual language of T3 Code
(`https://github.com/pingdotgg/t3code`): neutral alpha-based surface tokens,
the inset rounded main-stage card, and the SVG grain texture data URL are
adapted from that project. T3 Code is available under the MIT License:

MIT License

Copyright (c) 2026 T3 Tools Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## DeepSeek-Reasonix runtime

The DwellProof desktop package bundles the pinned Reasonix CLI binary
(`esengine/DeepSeek-Reasonix`, v1.17.11, commit
`20a64b4d15687fbddb7ccc658daf909f71d01427`) as a read-only explanation layer.
Reasonix is available under the MIT License; the upstream license text is
bundled as `LICENSE.reasonix` inside the application package. The ACP host,
isolation, and policy code in `src-tauri/src/reasonix/` are DwellProof
originals informed by COFORGE's documented approach (see the COFORGE notice
above).

## DM Sans typeface

The workbench bundles the DM Sans variable font (Latin subsets) as
self-hosted WOFF2 files under `web/public/fonts/`, sourced from the
`@fontsource-variable/dm-sans` npm package. DM Sans is licensed under the
SIL Open Font License, Version 1.1:

Copyright 2014 The DM Sans Project Authors
(`https://github.com/googlefonts/dm-fonts`).

The complete license text is retained in `licenses/DM-Sans-OFL.txt`.

## Other dependencies and source material

Package dependencies retain the licenses declared by their respective
projects. Research snapshots, quotations, public data, and archival material
remain subject to the rights and source terms described in `RIGHTS.md`.
