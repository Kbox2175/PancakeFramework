import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

import tempfile


def test_yaml_basic_load():
    from resource.yml import yaml_init
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = os.path.join(tmpdir, "resource", "yaml")
        os.makedirs(yaml_dir)
        with open(os.path.join(yaml_dir, "test.yaml"), "w") as f:
            f.write("app:\n  name: test\n  version: 1.0\n")
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        try:
            data = yaml_init()
            assert data["app.name"] == "test"
            assert data["app.version"] == 1.0
        finally:
            os.chdir(original_dir)


def test_yaml_placeholder_resolution():
    from resource.yml import yaml_init
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = os.path.join(tmpdir, "resource", "yaml")
        os.makedirs(yaml_dir)
        with open(os.path.join(yaml_dir, "test.yaml"), "w") as f:
            f.write("base:\n  name: app\nfull:\n  title: ${base.name} v1\n")
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        try:
            data = yaml_init()
            assert data["full.title"] == "app v1"
        finally:
            os.chdir(original_dir)


def test_yaml_circular_reference_no_crash():
    from resource.yml import yaml_init
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = os.path.join(tmpdir, "resource", "yaml")
        os.makedirs(yaml_dir)
        with open(os.path.join(yaml_dir, "test.yaml"), "w") as f:
            f.write("a:\n  val: ${b.val}\nb:\n  val: ${a.val}\n")
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        try:
            # Should not hang or crash
            data = yaml_init()
            assert isinstance(data, dict)
        finally:
            os.chdir(original_dir)
