#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

DEFAULT_MANIFEST="${ROOT_DIR}/config/matrix_sources.tsv"
MANIFEST="${1:-${DEFAULT_MANIFEST}}"
MATRIX_ROOT="${MATRIX_ROOT:-${ROOT_DIR}/matrices}"
FORCE="${FORCE:-0}"

usage() {
    cat <<USAGE
Usage: $0 [matrix_sources.tsv]

Manifest format, tab-separated:
  category  output_file.mtx  archive_url  [tar_member]

Blank lines and lines beginning with # are ignored.

Environment:
  MATRIX_ROOT=/path/to/matrices   output root, default: ${MATRIX_ROOT}
  FORCE=1                         overwrite existing .mtx files
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ ! -f "${MANIFEST}" ]]; then
    printf 'Manifest not found: %s\n' "${MANIFEST}" >&2
    exit 1
fi

if command -v curl >/dev/null 2>&1; then
    download() {
        local url="$1"
        local output="$2"
        curl -fL --retry 3 --connect-timeout 20 -o "${output}" "${url}"
    }
elif command -v wget >/dev/null 2>&1; then
    download() {
        local url="$1"
        local output="$2"
        wget -O "${output}" "${url}"
    }
else
    printf 'Neither curl nor wget is available.\n' >&2
    exit 1
fi

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "${value}"
}

select_member() {
    local archive="$1"
    local output_file="$2"
    local requested_member="$3"
    local member

    if [[ -n "${requested_member}" ]]; then
        if tar -tzf "${archive}" "${requested_member}" >/dev/null 2>&1; then
            printf '%s\n' "${requested_member}"
            return 0
        fi

        printf 'Requested tar member not found: %s\n' "${requested_member}" >&2
        return 1
    fi

    while IFS= read -r member; do
        if [[ "${member##*/}" == "${output_file}" ]]; then
            printf '%s\n' "${member}"
            return 0
        fi
    done < <(tar -tzf "${archive}" | awk '/\.mtx$/ {print}')

    printf 'Could not find %s inside %s\n' "${output_file}" "${archive}" >&2
    return 1
}

extract_matrix() {
    local archive="$1"
    local member="$2"
    local target="$3"
    local work_dir="$4"
    local extracted="${work_dir}/${member}"
    local partial="${target}.part"

    mkdir -p "$(dirname -- "${extracted}")" "$(dirname -- "${target}")"
    tar -xzf "${archive}" -C "${work_dir}" "${member}"

    if [[ ! -s "${extracted}" ]]; then
        printf 'Extracted matrix is missing or empty: %s\n' "${extracted}" >&2
        return 1
    fi

    if ! head -n 1 "${extracted}" | grep -q '^%%MatrixMarket'; then
        printf 'Extracted file does not look like Matrix Market: %s\n' "${extracted}" >&2
        return 1
    fi

    cp "${extracted}" "${partial}"
    mv "${partial}" "${target}"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

line_no=0
downloaded=0
skipped=0

while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
    line_no=$((line_no + 1))
    line="$(trim "${raw_line}")"

    if [[ -z "${line}" || "${line}" == \#* ]]; then
        continue
    fi

    IFS=$'\t' read -r category output_file url tar_member extra <<< "${raw_line}"
    category="$(trim "${category:-}")"
    output_file="$(trim "${output_file:-}")"
    url="$(trim "${url:-}")"
    tar_member="$(trim "${tar_member:-}")"
    extra="$(trim "${extra:-}")"

    if [[ -z "${category}" || -z "${output_file}" || -z "${url}" ]]; then
        printf 'Invalid manifest line %d: expected category, output file, and URL.\n' "${line_no}" >&2
        exit 1
    fi

    if [[ -n "${extra}" ]]; then
        printf 'Invalid manifest line %d: too many tab-separated fields.\n' "${line_no}" >&2
        exit 1
    fi

    if [[ "${output_file}" != *.mtx ]]; then
        output_file="${output_file}.mtx"
    fi

    target="${MATRIX_ROOT}/${category}/${output_file}"
    if [[ -s "${target}" && "${FORCE}" != "1" ]]; then
        printf 'Skipping existing %s\n' "${target#${ROOT_DIR}/}"
        skipped=$((skipped + 1))
        continue
    fi

    safe_name="${category}_${output_file%.mtx}"
    archive="${tmp_dir}/${safe_name}.tar.gz"
    extract_dir="${tmp_dir}/${safe_name}"

    printf 'Downloading %s\n' "${url}"
    download "${url}" "${archive}"

    member="$(select_member "${archive}" "${output_file}" "${tar_member}")"
    printf 'Extracting %s -> %s\n' "${member}" "${target#${ROOT_DIR}/}"
    extract_matrix "${archive}" "${member}" "${target}" "${extract_dir}"
    downloaded=$((downloaded + 1))
done < "${MANIFEST}"

printf 'Done. Downloaded: %d, skipped: %d, root: %s\n' "${downloaded}" "${skipped}" "${MATRIX_ROOT}"
