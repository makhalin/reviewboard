import nose
        try:
            import mercurial
        except ImportError:
            raise nose.SkipTest("Hg is not installed")
