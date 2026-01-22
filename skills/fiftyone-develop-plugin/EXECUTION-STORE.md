# Execution Store Patterns

## Contents
- [Overview](#overview)
- [Store Key Strategy](#store-key-strategy)
- [ExecutionStore API](#executionstore-api)
- [Caching Patterns](#caching-patterns)
- [State Management](#state-management)
- [Cache Invalidation](#cache-invalidation)
- [Best Practices](#best-practices)

---

## Overview

### Panel State vs Execution Store

| Storage | Lifetime | Use Case |
|---------|----------|----------|
| `ctx.panel.state` | Transient (resets on panel reload) | UI state, form values, selected tabs |
| `ctx.panel.data` | Transient (resets on panel reload) | Large data for plots, tables |
| `ctx.store()` | Persistent (survives sessions) | User configs, cached results, execution history |

```python
def on_load(self, ctx):
    # Transient: UI preferences
    ctx.panel.state.active_tab = "overview"
    ctx.panel.state.is_expanded = True

    # Transient: Plot data
    ctx.panel.data.chart_data = compute_chart_data(ctx.dataset)

    # Persistent: User configuration
    store = ctx.store(self._get_store_key(ctx))
    ctx.panel.state.config = store.get("user_config") or default_config()
```

---

## Store Key Strategy

Use namespaced keys to avoid conflicts between plugins and datasets:

```python
class MyPanel(foo.Panel):
    version = "v1"  # For migration support

    def _get_store_key(self, ctx):
        """Generate unique store key for this panel instance."""
        plugin_name = self.config.name.split("/")[-1]
        dataset_id = ctx.dataset._doc.id
        return f"{plugin_name}_store_{dataset_id}_{self.version}"

    def on_load(self, ctx):
        store = ctx.store(self._get_store_key(ctx))
        # ...
```

**Key components:**
- **Plugin name**: Extracted from config, avoids hardcoding
- **Dataset ID**: Prevents cross-dataset conflicts
- **Version**: Enables migration when schema changes

---

## ExecutionStore API

```python
store = ctx.store("my_store")

# Basic operations
value = store.get(key)                    # Returns value or None
store.set(key, value)                     # Persist (default policy)
store.set(key, value, ttl=3600)           # Expire in 1 hour
store.set(key, value, policy="evict")     # Can be cleared by clear_cache()
store.set_cache(key, value, ttl=3600)     # Convenience for evict policy

# Check and delete
exists = store.has(key)                   # Returns bool
deleted = store.delete(key)               # Returns bool

# List and clear
keys = store.list_keys()                  # Returns list of keys
store.clear()                             # Delete all keys
store.clear_cache()                       # Clear only evictable keys

# TTL and policy management
store.update_ttl(key, new_ttl)            # Update expiration
store.update_policy(key, "persist")       # Change eviction policy

# Metadata
metadata = store.get_metadata(key)        # {created_at, updated_at, expires_at}

# Real-time updates
subscription_id = store.subscribe(callback)
store.unsubscribe(subscription_id)
```

---

## Caching Patterns

### Template File Caching

Cache expensive file loads with modification time tracking:

```python
def _load_template(self, ctx, template_path):
    """Load template with caching based on file modification time."""
    store = ctx.store(self._get_store_key(ctx))
    cache_key = f"template_{hash(template_path)}"
    cached = store.get(cache_key)

    # Check if file has changed
    file_mtime = os.path.getmtime(template_path)
    if cached and cached.get("file_mtime") == file_mtime:
        return cached.get("data")

    # Load and cache
    with open(template_path, "r") as f:
        data = json.load(f)

    store.set(cache_key, {
        "data": data,
        "file_mtime": file_mtime,
        "cached_at": time.time(),
    })
    return data
```

### Computed Results Caching

Cache expensive computations with dependency tracking:

```python
def _get_statistics(self, ctx, params):
    """Get statistics with caching based on parameters."""
    store = ctx.store(self._get_store_key(ctx))

    # Create cache key from parameters
    params_hash = hash(json.dumps(params, sort_keys=True))
    cache_key = f"stats_{params_hash}"
    cached = store.get(cache_key)

    # Check if cache is still valid
    if cached and self._is_cache_valid(cached, ctx):
        return cached.get("result")

    # Compute and cache
    result = expensive_computation(ctx.dataset, params)

    store.set(cache_key, {
        "result": result,
        "params": params,
        "dataset_size": len(ctx.dataset),
        "cached_at": time.time(),
    })
    return result

def _is_cache_valid(self, cached, ctx):
    """Check if cache is still valid based on dataset changes."""
    cached_size = cached.get("dataset_size", 0)
    current_size = len(ctx.dataset)

    # Invalidate if dataset size changed significantly (>5%)
    if abs(current_size - cached_size) > cached_size * 0.05:
        return False

    return True
```

---

## State Management

### Robust State Saving

Validate before saving to prevent corruption:

```python
def _save_state(self, ctx):
    """Save state with validation."""
    store = ctx.store(self._get_store_key(ctx))

    content = {
        "config": ctx.panel.state.config,
        "preferences": ctx.panel.state.preferences,
        "version": self.version,
        "saved_at": time.time(),
    }

    # Ensure JSON serializability
    try:
        json.dumps(content)
        store.set("panel_state", content)
    except (TypeError, ValueError) as e:
        print(f"Warning: Could not save state: {e}")
```

### State Migration

Handle version changes gracefully:

```python
def _load_state(self, ctx):
    """Load state with version migration."""
    store = ctx.store(self._get_store_key(ctx))
    content = store.get("panel_state")

    if content is None:
        return self._default_state()

    # Migrate if version changed
    stored_version = content.get("version", "v0")
    if stored_version != self.version:
        content = self._migrate_state(content, stored_version)

    return content

def _migrate_state(self, content, from_version):
    """Migrate state between versions."""
    if from_version == "v0" and self.version == "v1":
        # Add new field with default
        content.setdefault("config", {})["new_option"] = "default"

    content["version"] = self.version
    return content
```

### Conditional State Loading

Load state based on conditions:

```python
def on_load(self, ctx):
    """Load state conditionally."""
    if ctx.dataset is None:
        return

    store = ctx.store(self._get_store_key(ctx))
    content = store.get("panel_state")

    if content is None:
        self._initialize_defaults(ctx)
    elif self._should_reload(content, ctx):
        self._initialize_smart_defaults(ctx, content)
    else:
        self._restore_state(ctx, content)

def _should_reload(self, content, ctx):
    """Check if state should be reloaded."""
    # Reload if dataset changed significantly
    stored_size = content.get("dataset_size", 0)
    current_size = len(ctx.dataset)
    return abs(current_size - stored_size) > stored_size * 0.1
```

---

## Cache Invalidation

### Pattern-Based Invalidation

```python
def _invalidate_cache(self, ctx, pattern=None):
    """Invalidate cache entries matching pattern."""
    store = ctx.store(self._get_store_key(ctx))

    if pattern:
        # Invalidate matching keys
        for key in store.list_keys():
            if pattern in key:
                store.delete(key)
    else:
        # Clear all cache entries (keeping persistent data)
        store.clear_cache()
```

### Time-Based Invalidation

```python
def _cleanup_old_cache(self, ctx, max_age_hours=24):
    """Remove cache entries older than max_age."""
    store = ctx.store(self._get_store_key(ctx))
    cutoff_time = time.time() - (max_age_hours * 3600)

    for key in store.list_keys():
        metadata = store.get_metadata(key)
        if metadata and metadata.get("updated_at", 0) < cutoff_time:
            store.delete(key)
```

### Dataset-Aware Invalidation

```python
def on_change_dataset(self, ctx):
    """Invalidate cache when dataset changes."""
    store = ctx.store(self._get_store_key(ctx))

    # Clear computed results that depend on dataset
    for key in store.list_keys():
        if key.startswith("stats_") or key.startswith("computed_"):
            store.delete(key)
```

---

## Best Practices

### 1. Store Key Naming

```python
# Use descriptive prefixes
"template_cache_{hash}"      # Cached templates
"computed_stats_{params}"    # Computed results
"user_config"                # User preferences
"execution_history"          # Operation history
```

### 2. Include Metadata

```python
store.set(cache_key, {
    "result": result,
    "cached_at": time.time(),
    "dataset_size": len(ctx.dataset),
    "params": params,
    "version": self.version,
})
```

### 3. Error Handling

```python
def _safe_get(self, ctx, key, default=None):
    """Safely get value with fallback."""
    try:
        store = ctx.store(self._get_store_key(ctx))
        value = store.get(key)
        return value if value is not None else default
    except Exception as e:
        print(f"Warning: Store access failed: {e}")
        return default
```

### 4. Performance Considerations

- Cache expensive operations (>100ms)
- Use TTL for time-sensitive data
- Implement cache size limits if needed
- Clean up old entries periodically

### 5. Security

- Validate cached data before use
- Consider data privacy implications
- Use `clear()` when user requests data deletion

---

## Quick Reference

```python
class MyOperator(foo.Operator):
    version = "v1"

    def _get_store_key(self, ctx):
        plugin_name = self.config.name.split("/")[-1]
        return f"{plugin_name}_{ctx.dataset._doc.id}_{self.version}"

    def execute(self, ctx):
        store = ctx.store(self._get_store_key(ctx))

        # Check cache
        cached = store.get("result")
        if cached and self._is_valid(cached, ctx):
            return cached["result"]

        # Compute
        result = self._compute(ctx)

        # Cache with metadata
        store.set("result", {
            "result": result,
            "cached_at": time.time(),
            "dataset_size": len(ctx.dataset),
        })

        return result
```
