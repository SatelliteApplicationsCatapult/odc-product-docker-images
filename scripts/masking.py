def mask_good_quality(ds, product):
    """
    Identify pixels with valid data (requires working with native resolution datasets)
    """

    if product.startswith('s2'):
        good_quality = (
            (ds.scene_classification == 4) | # mask in VEGETATION
            (ds.scene_classification == 5) | # mask in NOT_VEGETATED
            (ds.scene_classification == 6) | # mask in WATER
            (ds.scene_classification == 7)   # mask in UNCLASSIFIED
        )
    elif product.startswith('ls8'):
        good_quality = (
            (ds.pixel_qa == 322)  | # clear
            (ds.pixel_qa == 386)  |
            (ds.pixel_qa == 834)  |
            (ds.pixel_qa == 898)  |
            (ds.pixel_qa == 1346) |
            (ds.pixel_qa == 324)  | # water
            (ds.pixel_qa == 388)  |
            (ds.pixel_qa == 836)  |
            (ds.pixel_qa == 900)  |
            (ds.pixel_qa == 1348)
        )
    else:
        good_quality = (
            (ds.pixel_qa == 66)   | # clear
            (ds.pixel_qa == 130)  |
            (ds.pixel_qa == 68)   | # water
            (ds.pixel_qa == 132)
        )

    return good_quality
