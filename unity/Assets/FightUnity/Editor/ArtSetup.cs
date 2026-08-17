// Editor helpers for the render demo.
//   Tools > FightCore > Slice Animation Sheets  — configures + slices the PNGs.
//   Tools > FightCore > Create Demo Object       — adds a FightDemo to the scene.
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace FightUnity.Editor
{
    public static class ArtSetup
    {
        private const string AnimDir = "Assets/FightUnity/Resources/Animations";
        private const int FrameSize = 128; // fight_env FRAME_SIZE

        [MenuItem("Tools/FightCore/Slice Animation Sheets")]
        public static void SliceSheets()
        {
            var guids = AssetDatabase.FindAssets("t:Texture2D", new[] { AnimDir });
            int done = 0;

            foreach (var guid in guids)
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                if (importer == null) continue;

                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                if (tex == null) continue;

                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Multiple;
                importer.filterMode = FilterMode.Point;      // crisp pixel art
                importer.mipmapEnabled = false;
                importer.spritePixelsPerUnit = FrameSize;     // 128px sprite = 1 world unit

                int frames = Mathf.Max(1, tex.width / FrameSize);
                string baseName = System.IO.Path.GetFileNameWithoutExtension(path);

                var metas = new List<SpriteMetaData>(frames);
                for (int i = 0; i < frames; i++)
                {
                    metas.Add(new SpriteMetaData
                    {
                        name = $"{baseName}_{i}",
                        rect = new Rect(i * FrameSize, 0, FrameSize, FrameSize),
                        alignment = (int)SpriteAlignment.BottomCenter,
                        pivot = new Vector2(0.5f, 0f),
                    });
                }

#pragma warning disable CS0618 // spritesheet is deprecated but still the simplest slice API
                importer.spritesheet = metas.ToArray();
#pragma warning restore CS0618

                EditorUtility.SetDirty(importer);
                importer.SaveAndReimport();
                done++;
            }

            AssetDatabase.Refresh();
            Debug.Log($"[FightUnity] Sliced {done} animation sheet(s) into {FrameSize}px frames.");
        }

        [MenuItem("Tools/FightCore/Create Demo Object")]
        public static void CreateDemoObject()
        {
            var go = new GameObject("FightDemo");
            go.AddComponent<FightDemo>();
            Undo.RegisterCreatedObjectUndo(go, "Create FightDemo");
            Selection.activeGameObject = go;
            Debug.Log("[FightUnity] Added FightDemo. Press Play to run.");
        }
    }
}