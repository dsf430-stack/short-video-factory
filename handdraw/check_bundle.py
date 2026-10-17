"""Check reviewed assets with the unchanged official validators before dispatch."""
import argparse
import json
import sys
import tempfile
from pathlib import Path
from preparation import resolve_bundle, save_json


def check(official, topic, seconds, job_id, style=None):
    bundle=resolve_bundle(Path(__file__).parent/'prepared',topic,seconds,job_id,style)
    skill=Path(official).resolve()/'skills/sweety-handdraw-video'
    sys.path.insert(0,str(skill/'scripts'))
    from style_choice import verify_style
    from drawing_contract import verify_drawing_plans
    from art_direction import check_record, digest
    from stroke_assets import configure_assets, build_illustration
    story=json.loads((bundle/'story.json').read_text())
    actions=[]
    for scene in story['scenes']:
        actions.append({'type':'illustration','drawing_plan_id':scene['id'],
            'source':scene.get('source','inputs/'+scene['id']+'.png'),'parts':scene['parts'],
            **{key:scene[key] for key in ('crop','outline_mask') if key in scene}})
    manifest={'drawing_plan':'design/drawing-plan.json','drawing_review':'design/drawing-review.json',
              'pages':[{'beats':[{'text':scene['text'],'actions':[action]}]} for scene,action in zip(story['scenes'],actions)]}
    resolved=verify_style(bundle)
    verify_drawing_plans(bundle,manifest,resolved)
    sources=[(bundle/'inputs/cover.png',None)]+[(bundle/action['source'],action.get('crop')) for action in actions]
    check_record(bundle/'design/art-direction.json',sources,digest(skill/'dependencies/sweety-image-art-direction/GUIDE.md'),resolved['resolved_sha256'])
    with tempfile.TemporaryDirectory(prefix='sweety-parts-') as directory:
        configure_assets(directory,'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',3)
        for scene,action in zip(story['scenes'],actions):
            build_illustration(scene['id'],bundle/action['source'],scene.get('image_width',840),scene.get('image_height',840),
                crop=action.get('crop'),parts=action['parts'],
                outline_mask_path=bundle/action['outline_mask'] if action.get('outline_mask') else None)
            print('OFFICIAL_PART_CHECK_PASS',scene['id'],flush=True)
    request_path=bundle/'request.json'
    if request_path.exists():
        request=json.loads(request_path.read_text());request['state']='ASSETS_VALIDATED';save_json(request_path,request)
    return {'status':'ASSETS_VALIDATED','job_id':bundle.name,'style':resolved['name'],'illustrations':len(actions),'extra_model_api_used':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--official',required=True);p.add_argument('--topic',required=True)
    p.add_argument('--seconds',type=int,default=30);p.add_argument('--job-id',required=True);p.add_argument('--style')
    args=p.parse_args();print(json.dumps(check(**vars(args)),ensure_ascii=False))
