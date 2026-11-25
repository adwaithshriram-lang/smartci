# Assignment 4.2 — Smart Build-Cache Invalidation

**Student:** Adwaith Shri Ram  
**USN:** 24BTRAO001  
**Course:** B.Tech AI-Driven DevOps  
**Topic:** Smart Build-Cache Invalidation  
**Repository:** https://github.com/adwaithshriram-lang/smartci

## 1. Objective

To configure dependency caching in GitHub Actions and demonstrate a cache hit when the dependency input remains unchanged, followed by automatic cache invalidation when `requirements.txt` changes.

## 2. Background

GitHub-hosted jobs run on fresh virtual machines. Files installed during one job are not automatically present in the next job. A dependency cache stores reusable downloaded package data outside the temporary runner. A cache key identifies the input state. If the key matches, the cache can be restored; if the key changes, the job gets a cache miss and creates a new cache.

## 3. Implementation

The CI workflow uses `actions/cache@v4` to cache pip's download directory:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ hashFiles('requirements.txt') }}
```

The key contains a hash of `requirements.txt`. Therefore, the same dependency file produces the same key, while a dependency-file change produces a different key. The cache step is placed after Python setup and before package installation.

## 4. Demonstration procedure

1. Add the cache step to `.github/workflows/ci.yml` and push it. The first run is expected to show a cache miss because no matching cache exists yet. The job installs dependencies and saves the cache.
2. Push a harmless documentation change without changing `requirements.txt`. The next run uses the same key and is expected to restore the cache (cache hit).
3. Add `pytest-cov` to `requirements.txt` and push the change. The hash changes, so the previous cache key no longer matches. The run is expected to show a cache miss, install the updated dependencies, and save a new cache.
4. Inspect the Actions logs for the cache restore messages and confirm that the tests still execute.

## 5. How cache invalidation works

The expression `hashFiles('requirements.txt')` calculates a content-based hash from the dependency file. The cache key is not based only on the branch name or commit message. It is tied to the actual dependency specification. This prevents a cache built for an older dependency list from being treated as the current cache after dependencies change.

## 6. Observed results

The three GitHub Actions runs completed successfully:

| Demonstration | GitHub Actions run | Observed cache result | Outcome |
|---|---|---|---|
| Cache added | [Run #4](https://github.com/adwaithshriram-lang/smartci/actions/runs/45677084969) | Cache miss; no matching cache existed; cache saved with the original requirements hash | Success |
| Documentation-only commit | [Run #5](https://github.com/adwaithshriram-lang/smartci/actions/runs/45677136386) | Cache hit; approximately 3 MB restored successfully using the same key | Success |
| Dependency file changed | [Run #6](https://github.com/adwaithshriram-lang/smartci/actions/runs/45677152702) | New key generated; cache miss; new cache saved | Success |

The first and second runs used the same key, `pip-385f93110a217a06a247c64e1018c917fca8911c00ef1d79dab564651503dc67`. After adding `pytest-cov` to `requirements.txt`, the key changed to `pip-fe0c1a0877c73d175bde098029c48fa310aa6c830e6f17f305be16826257b14a`. This confirms that the cache was invalidated when the dependency input changed. All three workflow jobs and their test steps completed successfully.

## 7. Benefits

- Reduces repeated package downloads.
- Can shorten dependency installation time.
- Saves GitHub Actions runner time and network traffic.
- Uses a dependency hash to avoid reusing stale dependency caches.
- Keeps the cache across temporary GitHub-hosted runner machines.

## 8. Limitations

This implementation caches pip's downloaded package files; it does not cache the complete virtual environment or compiled application outputs. It is a deterministic hash-based cache invalidation demonstration, not a trained AI model. More advanced change-impact analysis can also use dependency graphs and semantic relationships.

## 9. Conclusion

The project demonstrates a practical build-cache strategy in GitHub Actions. A matching dependency hash allows the workflow to reuse cached package downloads. Changing `requirements.txt` changes the key and automatically invalidates the old cache for the new dependency state. This improves CI efficiency while preserving reproducible dependency installation.

## 10. Repository

https://github.com/adwaithshriram-lang/smartci
