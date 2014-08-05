```bash
# This page will go through one of the tests prepared for Publish. The
# goal is for each test to be built prior to developing Publish, and for
# Publish then to successfully publish each test once complete.

# This test is Maya-centric.
```

### Description

Publishing of a model from Maya.

- Resources are available [here][maya-resources]
- Root of project is `tests\Peter\model\maya`
- Working files are at `tests\Peter\model\maya\scenes`
- Published resources are at `tests\Peter\model\maya\published`

#### Validations

The following validations are run on this model.

- Ensure there are no empty meshes
- Ensure history is clean
- Look for unconnected intermediate objects

Reference: http://www.martintomoya.com/tools_info.html

#### Selection

![](https://dl.dropbox.com/s/ug972xdbe5e7wkf/test%2C-model.png)

An objectSet has been created containing the `diver_AST`, which is our INSTANCE, and `geometry_SEL`, an additional objectSet relevant to the INSTANCE. The following metadata has been applied to the objectSet:

```json
{
  "publishable": true,
  "class": "model"
}
```

`publishable` denotes this objectSet to be valid for publishing and will be detected by Publish.

```python
maya.cmds.ls('*.publishable', objectsOnly=True)
```

`class` denotes the type of validations that will be executed. In this case, the value is `model` which will limit the number of tests to those relevant to models.

#### Execute

Finally, Publish is run. It reads from `publishable` objectSets, performs tests as per `class` and stores the resulting resources within the current Maya project: `tests\Peter\model\maya\published`


[maya-resources]: https://github.com/abstractfactory/publish/tree/master/resources/tests/full/individual_assets/Peter/model