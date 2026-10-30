#!/bin/bash
# Builds demos/demo_repo_8 .. demos/demo_repo_15 from REAL bug-fix commits of open source projects.
# For each case: check out the commit just BEFORE the fix, then add only the test file
# that the fix commit added, so the new test fails. Run from inside bugfix-agent:
#   bash make_real_cases.sh
set -e

build() {  # build <folder> <github repo> <fix commit> <test files...>
  local name=$1 repo=$2 fix=$3; shift 3
  local dir="demos/$name" tmp="_tmp_$name"
  mkdir -p demos
  rm -rf "$dir" "$tmp"
  git clone -q --filter=blob:none "https://github.com/$repo.git" "$tmp"
  git -C "$tmp" checkout -q "$fix~1"
  for t in "$@"; do git -C "$tmp" show "$fix:$t" > "$tmp/$t"; done
  rm -rf "$tmp/.git" "$tmp/.github" "$tmp/docs"
  mv "$tmp" "$dir"
  echo "$repo @ $fix~1 (fix commit: $fix)" > "$dir/CASE_SOURCE.txt"
  echo "built $dir from $repo"
}

# 8: more-itertools (MIT). Bug in a ~5000-line module: falsy user exception is dropped.
build demo_repo_8  more-itertools/more-itertools def2dabea858b6ecb84ee0c52e6e07929f2c409c tests/test_more.py
# 9: boltons (BSD). Bug spans two modules (listutils + setutils), two test files.
build demo_repo_9  mahmoud/boltons e00c10a809525027b8167fbb7ac233cfc25a01f5 tests/test_listutils.py tests/test_setutils.py
# 10: toolz (BSD). interpose([]) raises StopIteration.
build demo_repo_10 pytoolz/toolz d2eba0374a452c2b18fe188b04527e22bda3548c toolz/tests/test_itertoolz.py

# 11: requests (Apache-2.0). get_netrc_auth returns empty credentials from a bare "default" entry.
build demo_repo_11 psf/requests 47914226c2968802f2cdee3f6f0f6e06e4472f64 tests/test_utils.py

# 12: click (BSD-3-Clause). HelpFormatter.write_usage with no args drops the prefix (issue #3360).
build demo_repo_12 pallets/click 0551bf53588ae87f462d336f24f853a156fefe3a tests/test_formatting.py

# 13: marshmallow (MIT). validate.Email rejects internationalized domain names (IDNs).
build demo_repo_13 marshmallow-code/marshmallow f07eadc87dfac25ed505d5cd9d186920f2682733 tests/test_validate.py

# 14: sortedcontainers (Apache-2.0). SortedList.update() orders equal keys differently than add().
build demo_repo_14 grantjenks/python-sortedcontainers 7dc426c95a0c329d5514e6198d92080f1ffc1e5e tests/test_coverage_sortedkeylist_modulo.py tests/test_coverage_sortedkeylist_negate.py

# 15: tabulate (MIT). tabulate([], maxcolwidths=N) raises on empty data (issue #180).
build demo_repo_15 astanin/python-tabulate 20c6370d5da2dae89b305bfb6c7f12a0f8b7236c test/test_regression.py

echo "Done. Each folder keeps its original LICENSE file; keep it."