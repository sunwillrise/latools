# LAtools + Range selection feature

## About this feature
* LAtools is an amazing tool for LA-ICP-MS data reduction created by Oscar Branson.
(https://github.com/oscarbranson/latools)
* However, when I used this LAtools to reduce my own data, I realized that the existing `filters` were not very useful for my data. I really needed to **select the ranges of the signal manually** to exclude/include small inclusions.
* I understand that this feature is not something Dr. Oscar intended; That's why I made it into separete branch in a separate repository.
* Also, there are some **bugfix** included in this version, most of them I already reported [here](https://github.com/oscarbranson/latools/issues)


## How to use  
### How to exclude inclusions in SRM
* Unfortunately, some elements in some SRMs are not completely homogenus. Let's say you hit the inclusions in the first SRM like this;
![Sorry!](/fig/inclusion-sample-1.png)

* First, you can do this to know the currently selected region. If the `startIndex` is 56 and the `endIndex` is 95 that means the current signal region is from the 56th data point to 95th data point in this data file.
```
eg.stds[0].filter_select_range()
>>>startIndex = 56 endIndex=95

```

* Then you can do like:
```
eg.stds[0].filter_select_range(startIndex=59, endIndex=75)
eg.stds[0].filt.on(filt='59-75')
eg.stds[0].tplot(analytes = 'Cu63', filt = True, ranges=True)
```
![Sorry again!](/fig/inclusion-sample-2.png)
Now the inclusion in the right area is excluded.

* If you don't like the filtered range, of course you can turn it off by using `eg.stds[0].filt.off()`

* When you want to calibrate the data with the active filters, do
```
eg.calibrate(srmfilt=True)
```
* Be aware that the filters applied for the SRMs does not appear in `eg.filter_status()`


### How to calculate the sample stats with a given region
* Sometimes you want to calculate both the stats with inclusion and without exclusion for some samples. For example, you want to calculate the data both with inclusion and without inclusion like this:

| Sample   | Cu | Ag |
|----------|----|----|
|1         | -  | -  |
|2-with-inc| -  | -  |
|2-excl-inc| -  | -  |
|3         | -  | -  |
|4         | -  | -  |

* First, you run,
```
a = eg.sample_branch_prepare(samples = ['2'])
```
By default, it generates numpy array containing two sample names: '2-with-inc' and '2-excl-inc'.

If you do
```
a = sample_branch_prepare(samples = ['2'], double=False)
```
it generates numpy array containing one sample name: '2-selected'.
You can also choose your favorite name by filling the `newfnames` parameter.

* Then you do
```
eg.sample_branch_append(a, ['2', '2'])
```
`a` is the array of the new sample names we just generated.
['2', '2'] is the list of original samples corresponds to the sample names.
By doing this two E object named '2-with-inc' and '2-excl-inc' is added to the original `analyse` object (`eg`).

* E object is the inheritance class of D object. You can use all the method written for D object. When the E object is initialized by `sample_branch_append()` it is a simple copy of the original D object of the given sample, and all the calculated value is already in there. However, once generated, E object is independent from the original D object, and you can apply different filters/methods to obtain stats.

  







 

