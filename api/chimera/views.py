import json
import os

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from api.chimera import chimera_bp
from api.chimera.forms import ChimeraConfigForm
from db import cc as running_config
from db.models import ChimeraConfig

basedir = os.path.join(os.path.dirname(__file__), '..', '..', 'db')
engine = create_engine('sqlite:///' + os.path.join(basedir, 'db.sqlite?check_same_thread=False'))
session = scoped_session(sessionmaker(bind=engine))



@chimera_bp.route('/configure', methods=['GET', 'POST'])
def configure():
    form = ChimeraConfigForm()
    cc = session.query(ChimeraConfig).first()

    if request.method == 'POST':
        form.populate_obj(cc)
        cc.audio_services = cc.audio_services.lower()
        try:
            json.loads(cc.playlist_folder_naming_scheme)
        except Exception as e:
            flash('Playlist folder scheme wrong!', 'error')

        try:
            json.loads(cc.folder_naming_scheme)
        except Exception as e:
            flash('Folder naming scheme wrong!', 'error')

        session.commit()
        flash('Config saved!')

        # update running config, may break
        form.populate_obj(running_config)
        running_config.audio_services = running_config.audio_services.lower()
        return redirect(url_for('chimera_bp.configure'))

    form.process(obj=cc)
    return render_template('configure.html', form=form)
