# Datasets bundled with QuantumScope

QuantumScope's code is MIT-licensed. The datasets in this folder are **not** covered by that licence: each keeps its own licence, listed below, and is redistributed under its terms with attribution. They are used offline, for teaching quantum machine learning.

| File | Dataset | Licence | Source and citation |
|---|---|---|---|
| iris.npz | Iris: 150 samples, 4 features, 3 classes | CC BY 4.0 | Fisher, R. (1936). Iris [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C56C76 |
| wine.npz | Wine: 178 samples, 13 features, 3 classes | CC BY 4.0 | Aeberhard, S. & Forina, M. (1992). Wine [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5PC7J |
| breast_cancer.npz | Breast Cancer Wisconsin (Diagnostic): 569 samples, 30 features, 2 classes | CC BY 4.0 | Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic) [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B |
| digits.npz | Optical Recognition of Handwritten Digits, test set: 1,797 images, 8×8, 10 classes | CC BY 4.0 | Alpaydin, E. & Kaynak, C. (1998). Optical Recognition of Handwritten Digits [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C50P49 |
| mnist.npz | MNIST, a subset: the first 200 images of each digit from the 10,000-image test set (2,000 images, 28×28); `index` gives each image's position in the original test set | CC BY-SA 3.0 | LeCun, Y., Cortes, C., & Burges, C. J. C. The MNIST database of handwritten digits. Copyright © Yann LeCun and Corinna Cortes. |
| fashion_mnist.npz | Fashion-MNIST, a subset: the first 200 images of each of the 10 classes from the 10,000-image test set (2,000 images, 28×28); `index` gives each image's position in the original test set | MIT | Xiao, H., Rasul, K., & Vollgraf, R. (2017). Fashion-MNIST: a novel image dataset for benchmarking machine learning algorithms. arXiv:1708.07747. Copyright © 2017 Zalando SE (https://github.com/zalandoresearch/fashion-mnist) |
| penguins.csv | Palmer Penguins: 344 penguins, 3 species, 4 measurements, island, sex and year (19 values missing) | CC0 1.0 | Horst, A. M., Hill, A. P., & Gorman, K. B. (2020). palmerpenguins: Palmer Archipelago (Antarctica) penguin data. R package version 0.1.0. https://doi.org/10.5281/zenodo.3960218. Data collected by Dr. Kristen Gorman and the Palmer Station Long Term Ecological Research Program |
| seeds.npz | Seeds: 210 wheat kernels, 7 features, 3 varieties (Kama, Rosa, Canadian) | CC BY 4.0 | Charytanowicz, M., Niewczas, J., Kulczycki, P., Kowalski, P., & Lukasik, S. (2010). Seeds [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5H30K |
| glass.npz | Glass Identification: 214 fragments, 9 features, 6 types (the original type 4, vehicle windows not float processed, has no samples) | CC BY 4.0 | German, B. (1987). Glass Identification [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5WW2P |

**Licences:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ · CC BY-SA 3.0, https://creativecommons.org/licenses/by-sa/3.0/ · CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ · MIT (Fashion-MNIST), reproduced below.

**About the MNIST subset:** mnist.npz is an adaptation of the MNIST database and is itself licensed under CC BY-SA 3.0. Its source files (t10k-images-idx3-ubyte.gz and t10k-labels-idx1-ubyte.gz) were verified against their official MD5 checksums (9fb629c4189551a2d022fa330f9573f3 and ec29112dd5afa0611ce80d1b7f02629c) before the subset was made.

**How the files were made:** the four UCI datasets come from the copies distributed with scikit-learn 1.9.1. They were checked against the UCI Repository's published sample and class counts (for example Iris 50/50/50, Wine 59/71/48, Breast Cancer 212 malignant / 357 benign, and the Digits test set's per-digit counts), and saved unchanged as NumPy .npz files.

**Added in v0.9.3:**
- **fashion_mnist.npz** was made from the official files t10k-images-idx3-ubyte.gz and t10k-labels-idx1-ubyte.gz (https://github.com/zalandoresearch/fashion-mnist), verified against their published MD5 checksums (bef4ecab320f06d8554ea6380940ec79 and bb300cfdad3c16e7a12a480ee83cd310). Class names follow the Fashion-MNIST documentation.
- **penguins.csv** is the package's `penguins.csv` (https://github.com/allisonhorst/palmerpenguins, inst/extdata), unchanged: 152 Adelie, 68 Chinstrap and 124 Gentoo penguins, with "NA" for missing values.
- **seeds.npz** and **glass.npz** come from copies of the UCI files (https://github.com/jbrownlee/Datasets, wheat-seeds.csv and glass.csv; Glass without its ID column), checked against the UCI Repository's published values: 210 Seeds samples, 70 per variety; 214 Glass samples with types 1, 2, 3, 5, 6, 7 counted 70, 76, 17, 13, 9, 29; and the first rows of both. Values are unchanged; class labels were renumbered from 0.

**Fashion-MNIST licence (MIT):**

The MIT License (MIT) Copyright © 2017 Zalando SE, https://tech.zalando.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
