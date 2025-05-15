#!/bin/bash

# 프로젝트 폴더 경로 설정
PROJECTS_DIR="./projects"

# 삭제할 파일 및 폴더 목록
FILES_TO_DELETE=(
  "diagram_breadboard.json.original"
  "diagram.json.original"
  "src/main.ino.original"
)
DIRS_TO_DELETE=(
  "backup"
)

PROJECT_FOLDERS=$(find "$PROJECTS_DIR" -mindepth 2 -maxdepth 2 -type d)

echo "Eunji Jeon: Starting to delete specified files and folders..."

for PROJECT in $PROJECT_FOLDERS; do
  echo "Eunji Jeon: Processing project folder: $PROJECT"
  
  for FILE in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$PROJECT/$FILE" ]; then
      echo "Eunji Jeon:   Deleting: $PROJECT/$FILE"
      rm "$PROJECT/$FILE"
    fi
  done
  
  for DIR in "${DIRS_TO_DELETE[@]}"; do
    if [ -d "$PROJECT/$DIR" ]; then
      echo "Eunji Jeon:   Deleting: $PROJECT/$DIR"
      rm -rf "$PROJECT/$DIR"
    fi
  done
done

echo "Eunji Jeon: Completed: All specified files and folders have been deleted."